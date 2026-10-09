#!/bin/sh
# Initializes the dev Garage node: cluster layout, a fixed S3 key and the s3dedup bucket.
# Idempotent, runs on every `docker compose up` as the garage-init service.
set -e

ADMIN="${GARAGE_ADMIN_URL:-http://garage:3902}"
AUTH="Authorization: Bearer ${GARAGE_ADMIN_TOKEN}"

api() {
    # api <endpoint> [json-body]
    if [ -n "$2" ]; then
        curl -sSf -X POST -H "$AUTH" -H "Content-Type: application/json" -d "$2" "$ADMIN/v2/$1"
    else
        curl -sSf -H "$AUTH" "$ADMIN/v2/$1"
    fi
}

# First string value of a JSON key (good enough for Garage admin API responses).
json_val() {
    grep -o "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed 's/.*"\([^"]*\)"$/\1/'
}

for i in $(seq 1 30); do
    api GetClusterStatus > /dev/null 2>&1 && break
    [ "$i" = 30 ] && { echo "Garage admin API not reachable at $ADMIN"; exit 1; }
    sleep 1
done

if api GetClusterLayout | grep -q '"roles"[[:space:]]*:[[:space:]]*\[\]'; then
    NODE_ID=$(api GetClusterStatus | json_val id)
    echo "Assigning layout to node $NODE_ID"
    api UpdateClusterLayout "{\"roles\":[{\"id\":\"$NODE_ID\",\"zone\":\"dev\",\"capacity\":10737418240,\"tags\":[]}]}" > /dev/null
    VERSION=$(api GetClusterLayout | grep -o '"version"[[:space:]]*:[[:space:]]*[0-9]*' | head -1 | sed 's/.*:[[:space:]]*//')
    api ApplyClusterLayout "{\"version\":$((VERSION + 1))}" > /dev/null
fi

if ! api "GetKeyInfo?id=$S3_ACCESS_KEY" > /dev/null 2>&1; then
    echo "Importing S3 key $S3_ACCESS_KEY"
    api ImportKey "{\"accessKeyId\":\"$S3_ACCESS_KEY\",\"secretAccessKey\":\"$S3_SECRET_KEY\",\"name\":\"oioioi-dev\"}" > /dev/null
fi

BUCKET_ID=$(api "GetBucketInfo?globalAlias=$BUCKET_NAME" 2>/dev/null | json_val id || true)
if [ -z "$BUCKET_ID" ]; then
    echo "Creating bucket $BUCKET_NAME"
    BUCKET_ID=$(api CreateBucket "{\"globalAlias\":\"$BUCKET_NAME\"}" | json_val id)
fi
api AllowBucketKey "{\"bucketId\":\"$BUCKET_ID\",\"accessKeyId\":\"$S3_ACCESS_KEY\",\"permissions\":{\"read\":true,\"write\":true,\"owner\":true}}" > /dev/null

echo "Garage ready: bucket $BUCKET_NAME, key $S3_ACCESS_KEY"

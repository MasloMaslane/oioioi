# Generated by Django 4.2.4 on 2023-09-03 11:37

from django.db import migrations, models
import django.db.models.deletion
import oioioi.participants.fields


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0011_alter_onsiteregistration_participant_and_more'),
        ('oi', '0006_auto_20210620_1806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='oiregistration',
            name='class_type',
            field=models.CharField(choices=[('1LO', 'pierwsza szkoły średniej'), ('2LO', 'druga szkoły średniej'), ('3LO', 'trzecia szkoły średniej'), ('4LO', 'czwarta szkoły średniej'), ('5LO', 'piąta szkoły średniej'), ('1G', 'pierwsza gimnazjum'), ('2G', 'druga gimnazjum'), ('3G', 'trzecia gimnazjum'), ('1SP', 'pierwsza szkoły podstawowej'), ('2SP', 'druga szkoły podstawowej'), ('3SP', 'trzecia szkoły podstawowej'), ('4SP', 'czwarta szkoły podstawowej'), ('5SP', 'piąta szkoły podstawowej'), ('6SP', 'szósta szkoły podstawowej'), ('7SP', 'siódma szkoły podstawowej'), ('8SP', 'ósma szkoły podstawowej')], max_length=7, verbose_name='class'),
        ),
        migrations.AlterField(
            model_name='oiregistration',
            name='participant',
            field=oioioi.participants.fields.OneToOneBothHandsCascadingParticipantField(on_delete=django.db.models.deletion.CASCADE, related_name='%(app_label)s_%(class)s', to='participants.participant'),
        ),
    ]
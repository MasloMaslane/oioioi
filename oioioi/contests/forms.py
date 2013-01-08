from django import forms
from django.contrib.admin import widgets
from django.forms.models import modelform_factory
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from oioioi.contests.models import Contest, ProblemInstance, Round, Submission
from oioioi.contests.utils import submitable_problem_instances

class SimpleContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'id', 'controller_name']

    start_date = forms.DateTimeField(widget=widgets.AdminSplitDateTime,
            label=_("Start date"))
    end_date = forms.DateTimeField(widget=widgets.AdminSplitDateTime,
            required=False, label=_("End date"))
    results_date = forms.DateTimeField(widget=widgets.AdminSplitDateTime,
            required=False, label=_("Results date"))

    def _generate_default_dates(self):
        now = timezone.now()
        self.initial['start_date'] = now
        self.initial['end_date'] = None
        self.initial['results_date'] = None

    def _set_dates(self, round):
        for date in ['start_date', 'end_date', 'results_date']:
            setattr(round, date, self.cleaned_data.get(date))

    def __init__(self, *args, **kwargs):
        super(SimpleContestForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            instance = kwargs['instance']
            rounds = instance.round_set.all()
            if len(rounds) > 1:
                raise ValueError("SimpleContestForm does not support contests "
                        "with more than one round.")
            if len(rounds) == 1:
                round = rounds[0]
                self.initial['start_date'] = round.start_date
                self.initial['end_date'] = round.end_date
                self.initial['results_date'] = round.results_date
            else:
                self._generate_default_dates()
        else:
            self._generate_default_dates()

    def clean(self):
        cleaned_data = super(SimpleContestForm, self).clean()
        round = Round()
        self._set_dates(round)
        round.clean()
        return cleaned_data

    def save(self, commit=True):
        instance = super(SimpleContestForm, self).save(commit=False)
        rounds = instance.round_set.all()
        if len(rounds) > 1:
            raise ValueError("SimpleContestForm does not support contests "
                    "with more than one round.")
        if len(rounds) == 1:
            round = rounds[0]
        else:
            instance.save()
            round = Round(contest=instance, name=_("Round 1"))
        self._set_dates(round)
        round.save()

        if commit:
            instance.save()

        return instance

class ProblemInstanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super(ProblemInstanceForm, self).__init__(*args, **kwargs)
        if instance:
            self.fields['round'].queryset = instance.contest.round_set

class SubmissionForm(forms.Form):
    problem_instance_id = forms.ChoiceField(label=_("Problem"))

    def __init__(self, request, *args, **kwargs):
        forms.Form.__init__(self, *args, **kwargs)

        self.request = request

        pis = submitable_problem_instances(request)
        pi_choices = [(pi.id, unicode(pi)) for pi in pis]
        pi_field = self.fields['problem_instance_id']
        pi_field.choices = pi_choices
        pi_field.widget.attrs['class'] = 'input-xlarge'

        request.contest.controller.adjust_submission_form(request, self)

    def clean(self):
        cleaned_data = forms.Form.clean(self)

        if 'problem_instance_id' not in cleaned_data:
            return cleaned_data

        try:
            pi = ProblemInstance.objects.filter(contest=self.request.contest) \
                    .get(id=cleaned_data['problem_instance_id'])
            cleaned_data['problem_instance'] = pi
        except ProblemInstance.DoesNotExist:
            self._errors['problem_instance_id'] = self.error_class([
                _("Invalid problem")])
            del cleaned_data['problem_instance_id']
            return cleaned_data

        submissions_number = Submission.objects \
            .filter(user=self.request.user, problem_instance__id=pi.id) \
            .count()
        submissions_limit = \
            self.request.contest.controller.get_submissions_limit()
        if submissions_limit and submissions_number >= submissions_limit:
            raise forms.ValidationError(_("Submission limit for the problem \
                '%s' exceeded." % (pi.problem.name,)))

        decision = self.request.contest.controller.can_submit(self.request, pi)
        if not decision:
            raise forms.ValidationError(str(decision.exc))

        return self.request.contest.controller \
                .validate_submission_form(self.request, pi, self, cleaned_data)

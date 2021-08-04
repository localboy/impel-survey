import argparse
import logging

from django import forms
from django.forms import models
from django.urls import reverse
from django.utils.text import slugify

from survey.models import Answer, QuestionType, Question, Response

LOGGER = logging.getLogger(__name__)


class ResponseForm(models.ModelForm):
    """
    Gererating survey respose form for user input corresponding 
    to survey questions and their type.
    """
    FIELDS = {
        QuestionType.TEXT: forms.CharField,
        QuestionType.SELECT: forms.MultipleChoiceField,
    }

    WIDGETS = {
        QuestionType.TEXT: forms.Textarea,
        QuestionType.RADIO: forms.RadioSelect,
        QuestionType.SELECT: forms.CheckboxSelectMultiple,
    }

    class Meta:
        model = Response
        fields = ()

    def __init__(self, *args, **kwargs):
        """
        Expects a survey object to be passed in initially
        """
        self.survey = kwargs.pop("survey")
        self.user = kwargs.pop("user")
        self.session_data = kwargs.pop('session_data')
        try:
            self.step = int(kwargs.pop("step"))
        except KeyError:
            self.step = None
        super().__init__(*args, **kwargs)

        self.steps_count = len(self.survey.questions.all())
        self.response = False
        self.answers = False

        self.add_questions(kwargs.get("data"))

        self._get_preexisting_response()

        if self.response is not None:
            for name in self.fields.keys():
                self.fields[name].widget.attrs["disabled"] = True

    def add_questions(self, data):
        """
        Add a field for each survey question, corresponding to the question
        type as appropriate.
        """

        for i, question in enumerate(self.survey.questions.all()):
            not_to_keep = i != self.step and self.step is not None
            if not_to_keep:
                continue
            self.add_question(question, data)

    def _get_preexisting_response(self):
        """
        Recover a pre-existing response in database.The user must be
        logged. Will store the response retrieved in an attribute to
        avoid multiple db calls.

        :rtype: Response or None"""
        if self.response:
            return self.response

        if not self.user.is_authenticated:
            self.response = None
        else:
            try:
                self.response = Response.objects.prefetch_related(
                    "user", "survey"
                ).get(
                    user=self.user, survey=self.survey
                )
            except Response.DoesNotExist:
                self.response = None
        return self.response

    def _get_preexisting_answers(self):
        """Recover pre-existing answers in database.

        The user must be logged. A Response containing the Answer must exists.
        Will create an attribute containing the answers retrieved to avoid
        multiple db calls.

        :rtype: dict of Answer or None"""
        if self.answers:
            return self.answers

        response = self._get_preexisting_response()
        if response is None:
            self.answers = None
        try:
            answers = Answer.objects.filter(response=response
                                            ).prefetch_related("question")
            self.answers = {
                answer.question.id: answer for answer in answers.all()}
        except Answer.DoesNotExist:
            self.answers = None

        return self.answers

    def _get_preexisting_answer(self, question):
        """
        Recover a pre-existing answer in database.

        The user must be logged. A Response containing the Answer must exists.

        :param Question question: The question we want to recover in the
        response.
        :rtype: Answer or None
        """
        answers = self._get_preexisting_answers()
        answer = answers.get(question.id, None)
        if answer:
            return answer
        else:
            # Try to get answer from session data
            try:
                question_id = 'question_'+str(question.id)
                answer = argparse.Namespace()
                answer.body = self.session_data[question_id]
                return answer
            except KeyError:
                return None

    def get_question_initial(self, question, data):
        """Get the initial value that we should use in the Form

        :param Question question: The question
        :param dict data: Value from a POST request.
        :rtype: String or None"""
        initial = None
        answer = self._get_preexisting_answer(question)
        if answer:
            # Initialize the field with values from the database if any
            if question.question_type == QuestionType.SELECT:
                initial = []
                if answer.body == "[]":
                    pass
                elif "[" in answer.body and "]" in answer.body:
                    initial = []
                    unformated_choices = answer.body[1:-1].strip()
                    for unformated_choice in unformated_choices.split(","):
                        choice = unformated_choice.split("'")[1]
                        initial.append(slugify(choice))
                elif isinstance(answer.body, list):
                    initial = answer.body
                else:
                    # Only one element
                    initial.append(slugify(answer.body))
            else:
                initial = answer.body
        if data:
            # Initialize the field field from a POST request, if any.
            # Replace values from the database
            initial = data.get("question_%d" % question.pk)
        return initial

    def get_question_widget(self, question):
        """Return the widget we should use for a question.

        :param Question question: The question
        :rtype: django.forms.widget or None"""
        try:
            return self.WIDGETS[question.question_type]
        except KeyError:
            return None

    @staticmethod
    def get_question_choices(question):
        """Return the choices we should use for a question.

        :param Question question: The question
        :rtype: List of String or None"""
        qchoices = None
        if question.question_type in [QuestionType.RADIO, QuestionType.SELECT]:
            qchoices = question.get_choices()
        return qchoices

    def get_question_field(self, question, **kwargs):
        """
        Return the field we should use in our form.
        :param Question question: The question
        :param **kwargs: A dict of parameter properly initialized in
            add_question.
        :rtype: django.forms.fields
        """
        try:
            return self.FIELDS[question.question_type](**kwargs)
        except KeyError:
            return forms.ChoiceField(**kwargs)

    def add_question(self, question, data):
        """
        Add a question to the form.
        :param Question question: The question to add.
        :param dict data: The pre-existing values from a post request.
        """
        kwargs = {"label": question.text}
        initial = self.get_question_initial(question, data)
        if initial:
            kwargs["initial"] = initial
        choices = self.get_question_choices(question)
        if choices:
            kwargs["choices"] = choices
        widget = self.get_question_widget(question)
        if widget:
            kwargs["widget"] = widget
        field = self.get_question_field(question, **kwargs)

        self.fields["question_%d" % question.pk] = field

    def has_prev_step(self):
        if self.step > 0:
            return True
        return False

    def prev_step_url(self):
        """
        Getting previous url if has previous step
        """
        if self.has_prev_step():
            context = {"id": self.survey.id, "step": self.step - 1}
            return reverse("survey-detail-step", kwargs=context)

    def has_next_step(self):
        if self.step < self.steps_count - 1:
            return True
        return False

    def next_step_url(self):
        """
        Getting next url is has next step
        """
        if self.has_next_step():
            context = {"id": self.survey.id, "step": self.step + 1}
            return reverse("survey-detail-step", kwargs=context)

    def current_step_url(self):
        """
        Getting current url
        """
        return reverse("survey-detail-step",
                       kwargs={"id": self.survey.id, "step": self.step})

    def save(self, commit=True):
        """
        Save the response object.
        Recover an existing response from the database if any.
        There is only one response by logged user.
        """
        response = self._get_preexisting_response()

        if response is None:
            response = super().save(commit=False)
        response.survey = self.survey
        response.user = self.user
        response.save()

        # create an answer object for each question and associate it with this
        # response.
        for field_name, field_value in list(self.cleaned_data.items()):
            if field_name.startswith("question_"):
                q_id = int(field_name.split("_")[1])
                question = Question.objects.get(pk=q_id)
                answer = self._get_preexisting_answer(question)
                if answer is None:
                    answer = Answer(question=question)
                answer.body = field_value
                answer.response = response
                answer.save()
        return response

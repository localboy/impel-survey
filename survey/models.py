from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


QUESTION_CHOICE_HELP_TEXT = _(
    """
    The choices field is only used if the question type is 'radio' and 'select'. 
    Provide a comma-separated list of options for this question
    """
)


def validate_choices(choices):
    """Validate that there is at least two choices in choices
    :param String choices: question choices.
    """
    values = choices.split(',')
    empty = 0
    for value in values:
        if value.replace(" ", "") == "":
            empty += 1
    if len(values) < 2 + empty:
        raise ValidationError("Choices must contain more than one item.")


class QuestionType(models.TextChoices):
    TEXT = 'text', 'Text Input'
    RADIO = 'radio', 'Radio'
    SELECT = 'select', 'Select Multiple'


class Survey(models.Model):
    """
    Survey object is a collection of questions with limited time duration.
    """

    title = models.CharField(max_length=400)
    description = models.TextField()
    duration = models.IntegerField(help_text="Survey duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="surveys")

    class Meta:
        verbose_name = _("Survey")
        verbose_name_plural = _("Surveys")

    def get_absolute_url(self):
        return reverse("survey-detail", kwargs={"id": self.pk})

    def __str__(self):
        return str(self.title)


class Question(models.Model):
    """
    Question object can be three type text, radio and multiple select.
    For radio and select you need to input minmum 2 choices in the choices filed separated by coma.
    """

    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    question_type = models.CharField(
        max_length=20, choices=QuestionType.choices, default=QuestionType.TEXT
    )
    choices = models.TextField(
        help_text=QUESTION_CHOICE_HELP_TEXT, blank=True, null=True)

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")

    def save(self, *args, **kwargs):
        if self.question_type in [QuestionType.RADIO, QuestionType.SELECT]:
            validate_choices(self.choices)
        super().save(*args, **kwargs)

    def get_clean_choices(self):
        """
        Return split and stripped list of choices with no null values.
        """
        if self.choices is None:
            return []
        choices_list = []
        for choice in self.choices.split(","):
            choice = choice.strip()
            if choice:
                choices_list.append(choice)
        return choices_list

    def get_choices(self):
        """
        Return a tuple for the 'choices' argument of a form widget.
        """
        choices_list = []
        for choice in self.get_clean_choices():
            choices_list.append((slugify(choice, allow_unicode=True), choice))
        choices_tuple = tuple(choices_list)
        return choices_tuple

    def __str__(self):
        return f"Question {self.text}"


class Response(models.Model):
    """
    Response object collection of questions and answer
    """

    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="responses")
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response to {self.survey} by {self.user}"


class Answer(models.Model):
    """
    Answer is represented as user input of a survey
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_(
        "Question"), related_name="answers")
    response = models.ForeignKey(Response, on_delete=models.CASCADE, verbose_name=_(
        "Response"), related_name="answers")
    created = models.DateTimeField(_("Creation date"), auto_now_add=True)
    updated = models.DateTimeField(_("Update date"), auto_now=True)
    body = models.TextField(_("Content"), blank=True, null=True)

    def __init__(self, *args, **kwargs):
        try:
            question = Question.objects.get(pk=kwargs["question_id"])
        except KeyError:
            question = kwargs.get("question")
        body = kwargs.get("body")
        if question and body:
            self.check_answer_body(question, body)
        super().__init__(*args, **kwargs)

    def check_answer_body(self, question, body):
        """
        Check if the answer body is in question choices if the question is
        in Radio or Select type
        """
        if question.question_type in [QuestionType.RADIO, QuestionType.SELECT]:
            choices = question.get_clean_choices()
            if body:
                answers = [body]
            for answer in answers:
                if answer not in choices:
                    msg = f"Answer '{body}' should be in {choices} "
                    raise ValidationError(msg)

    def __str__(self):
        return f"{self.__class__.__name__} to \
            '{self.question}' : '{self.body}'"

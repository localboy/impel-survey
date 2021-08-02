from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
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
    choices = models.TextField(help_text=QUESTION_CHOICE_HELP_TEXT)

    class Meta:
        verbose_name = _("question")
        verbose_name_plural = _("questions")

    def save(self, *args, **kwargs):
        if self.question_type in [QuestionType.RADIO, QuestionType.SELECT]:
            validate_choices(self.choices)
        super().save(*args, **kwargs)

    def __str__(self):
        return "Question '{self.text}'"


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
        return "Response to {self.survey} by {self.user}"


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

    def __str__(self):
        return "{self.__class__.__name__} to '{self.question}' : '{self.body}'"

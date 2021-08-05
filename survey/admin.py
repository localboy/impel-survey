from django.contrib import admin

from survey.models import Answer, Question, Response, Survey


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "duration", "created_by", "created_at", "total_responses")
    list_filter = ("created_by", "created_at")
    inlines = [QuestionInline]


class AnswerBaseInline(admin.StackedInline):
    fields = ("question", "body")
    readonly_fields = ("question",)
    extra = 0
    model = Answer


class ResponseAdmin(admin.ModelAdmin):
    list_display = ("survey", "created_at", "user", "response_type")
    list_filter = ("survey", "response_type", "created_at")
    date_hierarchy = "created_at"
    inlines = [AnswerBaseInline]
    # specifies the order as well as which fields to act on
    readonly_fields = ("survey", "created_at", "updated_at","user")


admin.site.register(Survey, SurveyAdmin)
admin.site.register(Response, ResponseAdmin)

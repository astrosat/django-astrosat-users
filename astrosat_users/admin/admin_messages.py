from django.contrib import admin
from django.forms import ModelForm

from astrosat.admin import DateRangeListFilter

from astrosat_users.models import Message, MessageAttachment


class MessageAttachmentAdminForm(ModelForm):
    class Meta:
        model = MessageAttachment
        fields = "__all__"


class MessageAttachmentAdminInline(admin.TabularInline):
    model = MessageAttachment
    form = MessageAttachmentAdminForm
    extra = 0


class MessageAdminForm(ModelForm):
    """
    A custom Admin Form to make some of the fields prettier
    """
    class Meta:
        model = Message
        fields = (
            "read",
            "archived",
            "user",
            # "date",  # will be included b/c of "readonly_fields" below
            "sender",
            "title",
            "content",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update(
            {
                "cols": 80,
                "class": "vLargeTextField"
            }
        )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    inlines = (MessageAttachmentAdminInline, )
    list_display = ("title_for_list_display", "user", "date", "read")
    list_editable = ("read", )
    list_filter = (
        "read",
        "archived",
        "user",
        ("date", DateRangeListFilter),
    )
    readonly_fields = (
        "user",
        "date",
    )

    def title_for_list_display(self, obj):
        MAX_TITLE_LEN = 50
        return (obj.title[:MAX_TITLE_LEN] +
                '...') if len(obj.title) > MAX_TITLE_LEN else obj.title

    title_for_list_display.short_description = "TITLE"

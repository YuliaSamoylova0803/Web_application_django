from django import forms
from users.forms import StyleFormMixin
from .models import Recipient, Message, Mailing, MailingLog

class RecipientForm(StyleFormMixin, forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if Recipient.objects.filter(email=email).exists():
            raise forms.ValidationError("Получатель с таким email уже существует")
        return email

    class Meta:
        model = Recipient
        fields = ["full_name", "email", "comment"]


class MessageForm(StyleFormMixin, forms.ModelForm):
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if attachment.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError("Файл слишком большой. Максимальный размер - 5MB")
        return attachment

    class Meta:
        model = Message
        fields = ["subject_message", "message_body", "attachment"]


class MailingForm(StyleFormMixin, forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=Recipient.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        label="Получатели"
    )
    first_shipment = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    end_shipment = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Mailing
        fields = ["message", "recipients", "status", "is_active", "first_shipment", "end_shipment"]


class MailingLogForm(StyleFormMixin, forms.ModelForm):
    date_of_attempt = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'readonly': True}),
        required=False
    )

    class Meta:
        model = MailingLog
        fields = ["mailing", "recipient", "status"]

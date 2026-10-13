from .models import ReminderChannelChoice, ReminderTone

DEFAULT_RULES = [
    {
        'name': '3 Days Before Due Date',
        'trigger_offset_days': -3,
        'tone': ReminderTone.FRIENDLY,
        'channel': ReminderChannelChoice.EMAIL,
        'subject_template': 'Upcoming Due Date: Invoice {{invoice_number}} for {{client_name}}',
        'body_template': (
            'Hi {{client_name}},\n\n'
            'This is a friendly reminder that invoice {{invoice_number}} (${{amount}}) '
            'from {{freelancer_name}} is due in 3 days on {{due_date}}.\n\n'
            'You can view your invoice and settle online securely here:\n'
            '{{pay_link}}\n\n'
            'Thank you for your prompt business!\n\n'
            'Best regards,\n'
            '{{freelancer_name}}'
        )
    },
    {
        'name': 'On Due Date',
        'trigger_offset_days': 0,
        'tone': ReminderTone.POLITE_NUDGE,
        'channel': ReminderChannelChoice.EMAIL,
        'subject_template': 'Due Today: Invoice {{invoice_number}} (${{amount}})',
        'body_template': (
            'Hi {{client_name}},\n\n'
            'Invoice {{invoice_number}} for ${{amount}} is due today ({{due_date}}).\n\n'
            'Please take a moment to review and complete your payment online:\n'
            '{{pay_link}}\n\n'
            'If you have already initiated this transfer, thank you!\n\n'
            'Warm regards,\n'
            '{{freelancer_name}}'
        )
    },
    {
        'name': '3 Days Overdue',
        'trigger_offset_days': 3,
        'tone': ReminderTone.FIRM,
        'channel': ReminderChannelChoice.EMAIL,
        'subject_template': 'Payment Reminder: Invoice {{invoice_number}} is 3 days overdue',
        'body_template': (
            'Dear {{client_name}},\n\n'
            'We noticed that invoice {{invoice_number}} (${{amount}}) was due on {{due_date}} '
            'and remains outstanding.\n\n'
            'Please settle the pending balance as soon as possible via this secure link:\n'
            '{{pay_link}}\n\n'
            'Let us know if you need any adjustments or assistance.\n\n'
            'Sincerely,\n'
            '{{freelancer_name}}'
        )
    },
    {
        'name': '14 Days Overdue (Final Notice)',
        'trigger_offset_days': 14,
        'tone': ReminderTone.FINAL_NOTICE,
        'channel': ReminderChannelChoice.EMAIL,
        'subject_template': 'FINAL NOTICE: Overdue Invoice {{invoice_number}} (${{amount}})',
        'body_template': (
            'Dear {{client_name}},\n\n'
            'This is a final notice regarding invoice {{invoice_number}} (${{amount}}), '
            'which is now 14 days overdue from the original due date of {{due_date}}.\n\n'
            'Immediate settlement is required to prevent account suspension:\n'
            '{{pay_link}}\n\n'
            'If you have any urgent concerns regarding this invoice, please reply immediately.\n\n'
            'Sincerely,\n'
            '{{freelancer_name}}'
        )
    }
]

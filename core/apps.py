from copy import copy

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Python 3.14 compatibility patch for django.template.context copy
        from django.template import context as django_context

        def _base_context_copy(self):
            cls = self.__class__
            duplicate = cls.__new__(cls)
            duplicate.dicts = self.dicts[:]
            return duplicate

        def _context_copy(self):
            cls = self.__class__
            duplicate = cls.__new__(cls)
            duplicate.dicts = self.dicts[:]
            duplicate.render_context = copy(self.render_context)
            duplicate.template = self.template
            duplicate.template_name = getattr(self, 'template_name', None)
            duplicate.use_l10n = getattr(self, 'use_l10n', None)
            duplicate.use_tz = getattr(self, 'use_tz', None)
            return duplicate

        django_context.BaseContext.__copy__ = _base_context_copy
        django_context.Context.__copy__ = _context_copy

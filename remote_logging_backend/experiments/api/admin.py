from django.contrib import admin
from api.models import *

admin.site.register(CustomUser)

class ExperimentAdmin(admin.ModelAdmin):
    readonly_fields = (
        'last_run',
    )


admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(ExperimentRun)
admin.site.register(LogEntry)


from django.db import migrations, models


def backfill_event_details(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    alias = schema_editor.connection.alias
    for booking in Booking.objects.using(alias).select_related("event").iterator(chunk_size=500):
        Booking.objects.using(alias).filter(pk=booking.pk).update(
            event_title=booking.event.title,
            event_venue_name=booking.event.venue_name,
            event_venue_address=booking.event.venue_address,
            event_timezone=booking.event.timezone,
            event_start_at=booking.event.start_at,
            event_end_at=booking.event.end_at,
        )


class Migration(migrations.Migration):
    dependencies = [("bookings", "0001_initial")]

    operations = [
        migrations.AddField(model_name="booking", name="event_title", field=models.CharField(max_length=180, editable=False, null=True)),
        migrations.AddField(model_name="booking", name="event_venue_name", field=models.CharField(max_length=180, editable=False, null=True)),
        migrations.AddField(model_name="booking", name="event_venue_address", field=models.TextField(editable=False, null=True)),
        migrations.AddField(model_name="booking", name="event_timezone", field=models.CharField(max_length=64, editable=False, null=True)),
        migrations.AddField(model_name="booking", name="event_start_at", field=models.DateTimeField(editable=False, null=True)),
        migrations.AddField(model_name="booking", name="event_end_at", field=models.DateTimeField(editable=False, null=True)),
        migrations.RunPython(backfill_event_details, migrations.RunPython.noop),
        migrations.AlterField(model_name="booking", name="event_title", field=models.CharField(max_length=180, editable=False)),
        migrations.AlterField(model_name="booking", name="event_venue_name", field=models.CharField(max_length=180, editable=False)),
        migrations.AlterField(model_name="booking", name="event_venue_address", field=models.TextField(editable=False)),
        migrations.AlterField(model_name="booking", name="event_timezone", field=models.CharField(max_length=64, editable=False)),
        migrations.AlterField(model_name="booking", name="event_start_at", field=models.DateTimeField(editable=False)),
        migrations.AlterField(model_name="booking", name="event_end_at", field=models.DateTimeField(editable=False)),
    ]

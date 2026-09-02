from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.text import slugify


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValidationError("Enter a valid IANA timezone, such as Africa/Johannesburg.") from exc


def validate_image_size(value):
    max_size = 8 * 1024 * 1024
    if value.size > max_size:
        raise ValidationError("Event images must be 8 MB or smaller.")


class EventQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Event.Status.PUBLISHED)


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.CharField(max_length=320)
    description = models.TextField()
    venue_name = models.CharField(max_length=180)
    venue_address = models.TextField()
    timezone = models.CharField(
        max_length=64,
        default="Africa/Johannesburg",
        validators=[validate_timezone],
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="ZAR", editable=False)
    image = models.ImageField(
        upload_to="events/%Y/%m/",
        blank=True,
        validators=[validate_image_size],
        help_text="Upload a JPG, PNG, WebP, or GIF image up to 8 MB.",
    )
    image_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["start_at", "title"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")),
                name="event_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(capacity__gte=1),
                name="event_capacity_positive",
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="event_price_non_negative",
            ),
            models.CheckConstraint(
                condition=Q(currency="ZAR"),
                name="event_currency_zar",
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "The event must end after it starts."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._available_slug()
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def _available_slug(self):
        base = slugify(self.title)[:180] or "event"
        candidate = base
        suffix = 2
        while type(self).objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

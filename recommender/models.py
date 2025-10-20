# recommender/models.py

from django.db import models

# Define the ten major categories (Field Categories) for the new system architecture
FIELD_CHOICES = [
    ('TECH', 'Technology, Computing, & Data'),
    ('ENG', 'Engineering, Architecture, & Design'),
    ('BUS', 'Business, Management, & Economics'),
    ('HEALTH', 'Health, Life, & Natural Sciences'),
    ('SOCIAL', 'Social Sciences, Humanities, & Liberal Arts'),
    ('MEDIA', 'Communication, Media, & Creative Arts'),
    ('EDUC', 'Education & Library Science'),
    ('PUB', 'Public Service & Administration'),
    ('HOSP', 'Hospitality, Tourism, & Service Industries'),
    ('APPLIED', 'Applied, Technical, & Vocational Sciences'),
]
class University(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True) # For your info page
    
    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(help_text="A brief description of the course.")
    icon = models.CharField(max_length=50, default='book-open', help_text="Name of a Feather icon (e.g., 'cpu', 'pen-tool').")
    field_category = models.CharField(
        max_length=10, 
        choices=FIELD_CHOICES, 
        default='TECH',
        help_text="The broad category this course belongs to (used for Stage 1 recommendation)."
    )
    offering_universities = models.ManyToManyField(University, related_name='offered_courses', blank=True)
    # -------------------------------------
    top_schools = models.TextField(blank=True, help_text="Comma-separated list of top schools in Metro Manila for this course.")
    def __str__(self):
        return self.name

class Assessment(models.Model):
    # (The rest of your Assessment model remains exactly the same as before)
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Student Name (Optional)")
    school = models.CharField(max_length=200, verbose_name="School/University")
    shs_strand = models.CharField(max_length=50, verbose_name="SHS Strand")
    tvl_strand = models.CharField(max_length=50, blank=True, null=True, verbose_name="TVL Strand")
    interest_science = models.IntegerField(default=0)
    interest_arts = models.IntegerField(default=0)
    interest_teaching = models.IntegerField(default=0)
    interest_business = models.IntegerField(default=0)
    interest_tech = models.IntegerField(default=0)
    interest_design = models.IntegerField(default=0)
    interest_sports = models.IntegerField(default=0)
    interest_building = models.IntegerField(default=0)
    interest_nature = models.IntegerField(default=0)
    interest_leading = models.IntegerField(default=0)
    interest_helping = models.IntegerField(default=0)
    ability_logic = models.IntegerField(default=0)
    ability_creativity = models.IntegerField(default=0)
    ability_comm = models.IntegerField(default=0)
    ability_practical = models.IntegerField(default=0)
    ability_teamwork = models.IntegerField(default=0)
    ability_spatial = models.IntegerField(default=0)
    interest_detail = models.IntegerField(default=0)
    interest_policy = models.IntegerField(default=0)
    interest_research = models.IntegerField(default=0)
    recommended_course_1 = models.CharField(max_length=200, blank=True)
    recommended_course_2 = models.CharField(max_length=200, blank=True)
    recommended_course_3 = models.CharField(max_length=200, blank=True)
    feedback_rating_1 = models.IntegerField(null=True, blank=True)
    feedback_rating_2 = models.IntegerField(null=True, blank=True)
    feedback_rating_3 = models.IntegerField(null=True, blank=True)
    feedback_submitted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment for {self.name or 'Anonymous'} from {self.school}"
# recommender/models.py

from django.db import models

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
    description = models.TextField(blank=True, help_text="Admission process and tuition info.")
    
    def __str__(self):
        return self.name

class PersonaTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="The user-friendly persona label (e.g., 'Logical Problem Solver').")
    key_traits_json = models.JSONField(default=list, help_text="JSON list of key traits for weighting.")
    profile_json = models.JSONField(default=dict, help_text="JSON dictionary of ideal trait scores.")
    
    def __str__(self):
        return self.name

class CoursePersonaWeight(models.Model):
    course = models.ForeignKey('Course', 
                               on_delete=models.CASCADE, 
                               related_name='weights') 
                               
    persona_template = models.ForeignKey(PersonaTemplate, on_delete=models.CASCADE)
    weight_factor = models.IntegerField(default=1, help_text="Weight (1-5) to multiply this persona's influence.")
    class Meta:
        unique_together = ('course', 'persona_template')


class Course(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(help_text="A brief description of the course.")
    icon = models.CharField(max_length=50, default='book-open', help_text="Name of a Feather icon (e.g., 'cpu', 'pen-tool').")
    
    active_personas = models.ManyToManyField(
        PersonaTemplate, 
        through=CoursePersonaWeight, 
        related_name='courses_using_template', 
        blank=True,
        help_text="The set of base personas activated for this course with custom weights."
    )
    global_trait_overrides = models.TextField(
        blank=True, 
        help_text="Custom trait:score pairs (e.g., ability_logic:5, interest_detail:4) for global fine-tuning."
    )
    
    field_category = models.CharField(
        max_length=10, 
        choices=FIELD_CHOICES, 
        default='TECH',
        help_text="The broad category this course belongs to (used for Stage 1 recommendation)."
    )
    offering_universities = models.ManyToManyField(University, related_name='offered_courses', blank=True)
    top_schools = models.TextField(blank=True, help_text="Comma-separated list of top schools in Metro Manila for this course.")
    
    def __str__(self):
        return self.name

class Assessment(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Student Name (Optional)")
    school = models.CharField(max_length=200, verbose_name="School/University")
    shs_strand = models.CharField(max_length=50, verbose_name="SHS Strand")
    tvl_strand = models.CharField(max_length=50, blank=True, null=True, verbose_name="TVL Strand")
    base_persona_key = models.CharField(
        max_length=100, 
        default='Computer Science', 
        help_text="pls."
    )
    
    custom_trait_scores = models.TextField(
        blank=True, 
        help_text="change value."
    )
    
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
    interest_detail = models.IntegerField(default=0)
    interest_policy = models.IntegerField(default=0)
    interest_research = models.IntegerField(default=0)

    # Ability fields
    ability_logic = models.IntegerField(default=0)
    ability_creativity = models.IntegerField(default=0)
    ability_comm = models.IntegerField(default=0)
    ability_practical = models.IntegerField(default=0)
    ability_teamwork = models.IntegerField(default=0)
    ability_spatial = models.IntegerField(default=0)
    
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
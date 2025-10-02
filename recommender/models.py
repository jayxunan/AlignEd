from django.db import models

class Course(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(help_text="A brief description of the course.")
    icon = models.CharField(max_length=50, default='book-open', help_text="Name of a Feather icon (e.g., 'cpu', 'pen-tool').")

    def __str__(self):
        return self.name

class Assessment(models.Model):
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


    recommended_course_1 = models.CharField(max_length=200, blank=True)
    recommended_course_2 = models.CharField(max_length=200, blank=True)
    recommended_course_3 = models.CharField(max_length=200, blank=True)
    

    feedback_rating_1 = models.IntegerField(null=True, blank=True, help_text="Rating for the 1st recommendation")
    feedback_rating_2 = models.IntegerField(null=True, blank=True, help_text="Rating for the 2nd recommendation")
    feedback_rating_3 = models.IntegerField(null=True, blank=True, help_text="Rating for the 3rd recommendation")
    feedback_submitted = models.BooleanField(default=False)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment for {self.name or 'Anonymous'} from {self.school}"
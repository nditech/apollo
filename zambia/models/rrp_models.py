from django.db import models
from webapp.models import ChecklistResponse, Checklist
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from general_models import ZambiaIncidentResponse

# Create your models here.
class ZambiaChecklistResponse(ChecklistResponse):
    OPTIONS_A = (
        (1, 'Before 6am'),
        (2, 'At 6am'),
        (3, 'Between 6am and 7am'),
        (4, 'After 9am')
    )
    YES_NO = (
        (1, 'Yes'),
        (2, 'No')
    )
    YES_NO_NONE = (
        (1, 'Yes'),
        (2, 'No'),
        (3, 'No One in Queue')
    )
    OPTIONS_CB = (
        (1, '3 boxes present'),
        (2, '2 boxes present'),
        (3, '1 box present')
    )
    OPTIONS_CC = (
        (1, 'correct ballots'),
        (2, 'no ballots'),
    )
    OPTIONS_CD = (
        (1, 'correct ballots'),
        (2, 'wrong ballots'),
        (3, 'no ballots')
    )
    OPTIONS_K = (
        (1, 'None(0)'),
        (2, 'Few(1-5)'),
        (3, 'Some(6-25)'),
        (4, 'Many(26+)')
    )
    # setup
    A = models.IntegerField(blank=True, null=True, choices=OPTIONS_A, validators=[RegexValidator(r'[1-4]')], help_text='At what time did people start voting at your polling stream? (if voting has not commenced by 9am complete a critical incident form)')
    B = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Was the polling stream set up so that voters could mark their ballot in secret? (if "No" complete a critical incident form)')
    CA = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Did the polling stream have Indelible Markers')
    CB = models.IntegerField(blank=True, null=True, choices=OPTIONS_CB, validators=[RegexValidator(r'[1-3]')], help_text='Did the polling stream have Three Ballot Boxes (Presidential, Parliamentary/National Assembly and Local Government)')
    CC = models.IntegerField(blank=True, null=True, choices=OPTIONS_CC, validators=[RegexValidator(r'[1-2]')], help_text='Presidential Ballot Papers - Orange')
    CD = models.IntegerField(blank=True, null=True, choices=OPTIONS_CC, validators=[RegexValidator(r'[1-3]')], help_text='Parliamentary/National Assembly Ballot Papers - Red ')
    CE = models.IntegerField(blank=True, null=True, choices=OPTIONS_CC, validators=[RegexValidator(r'[1-3]')], help_text='Local Government Ballot Papers - Black and White')
    CF = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Official Stamp/Mark')
    CG = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Final Voters\' Register')
    CH = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Polling Booths')
    D = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='How many polling officials were present at the polling stream?')
    E = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='How many political party polling agents were present at the polling stream?')
    EA = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-3]')], help_text='Was a polling agent present for MMD?')
    EB = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Was a polling agent present for Patriotic Front?')
    EC = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Was a polling agent present for UPND?')
    F = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were uniformed police present at the polling stream?')
    G = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were all ballot boxes present shown to be empty before they were closed and sealed?(if "No" complete a critical incident form)')
    H = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='How many people are registered at the polling stream?')
    J = models.CharField(blank=True, null=True, max_length=100, validators=[RegexValidator(r'\d+')], help_text='What is the ECZ\'s six digit ID number of the polling station of your polling stream')
    
    # voting
    K = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people with a NRC and voter\'s card were not permitted to vote because their name did not appear on the voter\'s register')
    M = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people were permitted to vote even though they did not have their NRC and voter\'s card?')    
    N = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people were permitted to vote even though their name was not in the voter\'s register?')
    P = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people who requested assistance in voting were denied assistance?')    
    Q = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people were permitted to vote on behalf of someone other than themselves?')
    R = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people who voted were not marked with indelible ink?')    
    
    S = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='At any time, did any campaigning occur inside or near the polling stream?')
    T = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='At any time, were uniformed security personnel present in the polling stream without permission of the election officials?')
    U = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='At any time, were unauthorised persons permitted in the polling stream?')
    V = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were there any incidents of intimidation or violence at the polling stream? (if "Yes" complete a critical incident form)')
    W = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='At any time, was the voting process suspended for more than 30 minutes? (if "Yes" complete a critical incident form)')
    
    # closing
    X = models.IntegerField(blank=True, null=True, choices=OPTIONS_K, validators=[RegexValidator(r'[1-4]')], help_text='How many people were in still in the queue waiting to vote at 18h00?')    
    Y = models.IntegerField(blank=True, null=True, choices=YES_NO_NONE, validators=[RegexValidator(r'[1-3]')], help_text='Was everyone in the queue waiting to vote at 18h00 permitted to vote')
    Z = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Was anyone permitted to join the queue and vote after 18h00?')
    AA = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were the opening slots of all ballot boxes sealed closed after everyone had voted?')
    
    # counting
    AB   = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were all polling agents permitted to observe the counting of ballot papers? (if "No" complete a critical incident form)')
    AC   = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were any unauthorized persons present during counting? (if "Yes" complete a critical incident form)')
    AD   = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were there any incidents of intimidation during counting? (if "Yes" complete a critical incident form)')
    AEAA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Ballot Papers Received at Your Assigned Stream(Presidential)')
    AEAB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Ballot Papers Received at Entire Polling Station(Presidential )')
    AEBA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Unused Ballot Papers at Your Assigned Stream(Presidential )')
    AEBB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Unused Ballot Papers at Entire Polling Station(Presidential )')
    AECA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Issued Ballot Papers at Your Assigned Stream(Presidential )')
    AECB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Issued Ballot Papers at Entire Polling Station(Presidential )')
    AEDA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Spoilt Ballot Papers at Your Assigned Stream(Presidential )')
    AEDB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Spoilt Ballot Papers at Entire Polling Station(Presidential )')
    AEEA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Ballot Papers Found in the Ballot Box at Your Assigned Stream(Presidential )')
    AEEB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Ballot Papers Found in the Ballot Box at Entire Polling Station(Presidential )')
    AFAA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Rejected Ballot Papers at Your Assigned Stream(Presidential )')
    AFAB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Rejected Ballot Papers at Entire Polling Station(Presidential )')
    AFBA = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Disputed Ballots at Your Assigned Stream(Presidential )')
    AFBB = models.IntegerField(blank=True, default=0, null=True, validators=[RegexValidator(r'[\d+]')], help_text='Number of Disputed Ballots at Entire Polling Station(Presidential )')
    AGA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Rupiah Banda, MMD at Your Assigned Stream(Presidential)')
    AGB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Rupiah Banda, MMD at Entire Polling Station(Presidential )')
    AHA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Elias Chipimo, NAREP at Your Assigned Stream (Presidential)')
    AHB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Elias Chipimo, NAREP at Entire Polling Station(Presidential )')
    AJA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for HakaindeHichilema, UPND at Your Assigned Stream (Presidential)')
    AJB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for HakaindeHichilema, UPND at Entire Polling Station(Presidential )')
    AKA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for TilyenjiKaunda, UNIP at Your Assigned Stream (Presidential)')
    AKB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for TilyenjiKaunda, UNIP at Entire Polling Station(Presidential )')
    AMA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Ng\'anduMagande, NMP at Your Assigned Stream (Presidential)')
    AMB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Ng\'anduMagande, NMP at Entire Polling Station(Presidential )')
    ANA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Charles Milupi, ADD at Your Assigned Stream (Presidential)')
    ANB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Charles Milupi, ADD at Entire Polling Station(Presidential )')
    APA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Godfrey Miyanda, Heritage Party at Your Assigned Stream (Presidential)')
    APB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Godfrey Miyanda, Heritage Party at Your Assigned Stream (Presidential)')
    AQA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Fred Mutesa, ZED at Entire Polling Station(Presidential )')
    AQB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Fred Mutesa, ZED at Your Assigned Stream (Presidential)')
    ARA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Edith Nawakwi, FDD at Entire Polling Station(Presidential )')
    ARB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Edith Nawakwi, FDD at Your Assigned Stream (Presidential)')
    ASA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Michael Sata, Patriotic Front at Entire Polling Station(Presidential )')
    ASB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Votes for Michael Sata, Patriotic Front at Your Assigned Stream (Presidential)')
    ATA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Number of Rejected Ballot Papers at Entire Polling Station(Presidential )')
    ATB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Number of Rejected Ballot Papers at Your Assigned Stream (Presidential)')
    AUA = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Number of Disputed Ballots at Entire Polling Station(Presidential )')
    AUB = models.IntegerField(blank=True, null=True, validators=[RegexValidator(r'\d+')], help_text='Number of Disputed Ballots at Your Assigned Stream (Presidential)')
    AV = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Did you agree with the presidential results for your polling stream?')
    AW = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Did all polling agents present agree with the presidentialresults for your polling stream?')
    AX = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were all polling agents present given a copy of the official results for the polling station?')
    AY = models.IntegerField(blank=True, null=True, choices=YES_NO, validators=[RegexValidator(r'[1-2]')], help_text='Were the official results for the polling station posted for the public to see?')
    
    class Admin:
        list_display = ('',)
        search_fields = ('',)
    
    class Meta:
        app_label = 'zambia'

    def __unicode__(self):
        return str(self.checklist.id)

def checklist_callback(sender, **kwargs):
    if not hasattr(kwargs['instance'], 'response'):
        response = ZambiaChecklistResponse.objects.create(checklist=kwargs['instance'])

def incident_callback(sender, **kwargs):
    if not hasattr(kwargs['instance'], 'response'):
        response = ZambiaIncidentResponse.objects.create(incident=kwargs['instance'])

post_save.connect(checklist_callback, sender=Checklist)
post_save.connect(incident_callback, sender=Incident)
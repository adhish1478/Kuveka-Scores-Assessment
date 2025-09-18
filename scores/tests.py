from django.test import TestCase
from . import utils
from django.core.files.uploadedfile import SimpleUploadedFile


class UtilsTestCase(TestCase):

    def test_parse_leads_csv(self):

        csv_content = b"name,email,role\nJohn,john@example.com,CEO\n"
        file = SimpleUploadedFile("leads.csv", csv_content, content_type="text/csv")

        leads = utils.parse_leads_csv(file)

        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['name'], 'John')

    def test_industry_match(self):
        self.assertEqual(utils.industry_match("Fintech", ["Fintech"]), 20)
        self.assertEqual(utils.industry_match("fintech", ["financial services"]), 10)
        self.assertEqual(utils.industry_match("Retail", ["Healthcare"]), 0)

    def test_calculate_rule_score_complete(self):
        lead = [{
            'name': 'Alice',
            'role': 'CEO',
            'company': 'Acme',
            'industry': 'Fintech',
            'location': 'Bangalore',
            'linkedin_bio': 'Bio1'
        }]
        offer = {'ideal_use_cases': ['Fintech']}
        score = utils.calculate_rule_score(lead, offer)
        self.assertEqual(score, 50)

    def test_final_score_with_mocked_ai(self):
        # Mock AI function
        def mock_ai_intent_score(lead, offer):
            return 50, "High interest"

        utils.ai_intent_score = mock_ai_intent_score

        lead = [{
            'name': 'Alice',
            'role': 'CEO',
            'company': 'Acme',
            'industry': 'Fintech',
            'location': 'Bangalore',
            'linkedin_bio': 'Bio1'
        }]
        offer = {'ideal_use_cases': ['Fintech']}
        result = utils.final_score(lead, offer)
        self.assertEqual(result['name'], 'Alice')
        self.assertEqual(result['intent'], 'High')
        self.assertEqual(result['reasoning'], 'High interest')
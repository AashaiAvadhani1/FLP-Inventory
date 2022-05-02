from django.test import TestCase
from django.contrib.auth.models import User

from inventory.models import Item, Checkout, Checkin, Family, AgeRange
from django.http.request import QueryDict, MultiValueDict
from datetime import date, timedelta
from unittest.mock import patch

from google_auth_oauthlib.flow import Flow

class GenerateReportDriveTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_superuser(username='testuser', password='12345')
        user.save()

        family = Family.objects.create(lname="ValidFamily")
        family.save()

        item = Item.objects.create(name="ValidItem", quantity=5)
        item.save()

        ageRange = AgeRange.objects.create(low=3, high=5) # will have value 1
        ageRange.save()
    
    @patch('inventory.gdrive.build')
    def test_export_drive_checkin_report(self, mock_build):
        self.client.login(username='testuser', password='12345')

        # Add item transaction
        session = self.client.session
        session['transactions-in'] = ['[{"model": "inventory.itemtransaction", "pk": null, "fields": {"item": 1, "quantity": 2}}]']
        session.save()

        response = self.client.post('/checkin/', data={"checkin": ""}, follow=True)

        # Check if valid
        self.assertEqual(response.status_code, 200)

        # Check if created
        self.assertEqual(Checkin.objects.filter().count(), 1)

        # Check for message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Checkin created.')

        today = date.today()
        weekAgo = today - timedelta(days=7)
        dictionary = {
            'tx-type': ['Checkin'],
            'start-date': [weekAgo.strftime('%Y-%m-%d')], 
            'end-date': [today.strftime('%Y-%m-%d')], 
            'csrfmiddlewaretoken': ['gorIARWkwGHd78mWsRPmvQIGcaE6FGtCxmo0tWApqHWmxKN35j6zUeI5R8yysl5R'], 
            'export_drive_table': ['']
        }

        qdict = QueryDict('', mutable=True)
        qdict.update(MultiValueDict(dictionary))

        fakeLink, fakeState = ("https://testworks.com", "testworks")
        fakeURI = 'https://flpinventory.com/report/'
        fakeCode = 'fakeCode'
    
        mock_build.return_value.files.return_value.create.return_value.execute.return_value = {
            'values': []}
        with patch.object(Flow, 'from_client_secrets_file') as patch_get_flow_obj:
            with patch.object(patch_get_flow_obj.return_value, 'authorization_url', return_value=(fakeLink, fakeState)) as patch_get_auth_url:
                response = self.client.post('/report/', qdict)
                patch_get_flow_obj.assert_called()
                patch_get_auth_url.assert_called()
                self.assertRedirects(response, fakeLink, fetch_redirect_response=False)
                self.assertEqual(patch_get_auth_url.return_value, (fakeLink, fakeState))
                self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
                self.assertEqual(response.status_code, 302)
                with patch.object(patch_get_flow_obj.return_value, 'fetch_token') as patch_fetch_token:
                    response = self.client.get('/report/', data={'code': fakeCode}, follow = True)

        # Check if valid
        self.assertEqual(patch_get_flow_obj.call_count, 2)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        patch_fetch_token.assert_called_with(code=fakeCode)
        mock_build.assert_called_with('drive', 'v3', credentials=patch_get_flow_obj.return_value.credentials)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/reports/generate_report.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['displaySuccessMessage'], True)
        self.assertEqual(response.context['tx_type'], 'Checkin')
        self.assertEqual(response.context['endDate'], today.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['startDate'], weekAgo.strftime('%Y-%m-%d'))
    
    @patch('inventory.gdrive.build')
    def test_export_drive_checkout_report(self, mock_build):
        self.client.login(username='testuser', password='12345')
        # Add item transaction
        session = self.client.session
        session['transactions-out'] = ['[{"model": "inventory.itemtransaction", "pk": null, "fields": {"item": 1, "quantity": 2}}]']
        session.save()

        response = self.client.post('/checkout/', data={"checkout": "", "family": "ValidFamily : (None)", "child": "Big Chungus", "age": "1"}, follow=True)

        # Check if valid
        self.assertEqual(response.status_code, 200)

        # Check if created
        self.assertEqual(Checkout.objects.filter().count(), 1)

        # Check for message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Checkout created.')

        today = date.today()
        weekAgo = today - timedelta(days=7)
        dictionary = {
            'tx-type': ['Checkout'],
            'start-date': [weekAgo.strftime('%Y-%m-%d')], 
            'end-date': [today.strftime('%Y-%m-%d')], 
            'csrfmiddlewaretoken': ['gorIARWkwGHd78mWsRPmvQIGcaE6FGtCxmo0tWApqHWmxKN35j6zUeI5R8yysl5R'], 
            'export_drive_table': ['']
            }

        qdict = QueryDict('', mutable=True)
        qdict.update(MultiValueDict(dictionary))

        fakeLink, fakeState = ("https://testworks.com", "testworks")
        fakeURI = 'https://flpinventory.com/report/'
        fakeCode = 'fakeCode'

        mock_build.return_value.files.return_value.create.return_value.execute.return_value = {
            'values': []}
        with patch.object(Flow, 'from_client_secrets_file') as patch_get_flow_obj:
            with patch.object(patch_get_flow_obj.return_value, 'authorization_url', return_value=(fakeLink, fakeState)) as patch_get_auth_url:
                response = self.client.post('/report/', qdict)
                patch_get_flow_obj.assert_called()
                patch_get_auth_url.assert_called()
                self.assertRedirects(response, fakeLink, fetch_redirect_response=False)
                self.assertEqual(patch_get_auth_url.return_value, (fakeLink, fakeState))
                self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
                self.assertEqual(response.status_code, 302)
                with patch.object(patch_get_flow_obj.return_value, 'fetch_token') as patch_fetch_token:
                    response = self.client.get('/report/', data={'code': fakeCode}, follow = True)

        # Check if valid
        self.assertEqual(patch_get_flow_obj.call_count, 2)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        patch_fetch_token.assert_called_with(code=fakeCode)
        mock_build.assert_called_with('drive', 'v3', credentials=patch_get_flow_obj.return_value.credentials)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/reports/generate_report.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['displaySuccessMessage'], True)
        self.assertEqual(response.context['tx_type'], 'Checkout')
        self.assertEqual(response.context['endDate'], today.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['startDate'], weekAgo.strftime('%Y-%m-%d'))
    
    @patch('inventory.gdrive.build')
    def test_export_drive_checkingbi_report(self, mock_build):
        self.client.login(username='testuser', password='12345')

        # Add item transaction
        session = self.client.session
        session['transactions-in'] = ['[{"model": "inventory.itemtransaction", "pk": null, "fields": {"item": 1, "quantity": 2}}]']
        session.save()

        response = self.client.post('/checkin/', data={"checkin": ""}, follow=True)

        # Check if valid
        self.assertEqual(response.status_code, 200)

        # Check if created
        self.assertEqual(Checkin.objects.filter().count(), 1)

        # Check for message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Checkin created.')

        today = date.today()
        weekAgo = today - timedelta(days=7)
        dictionary = {
            'tx-type': ['Checkin'],
            'start-date': [weekAgo.strftime('%Y-%m-%d')], 
            'end-date': [today.strftime('%Y-%m-%d')], 
            'itemizedOutput': ['itemized'],
            'csrfmiddlewaretoken': ['gorIARWkwGHd78mWsRPmvQIGcaE6FGtCxmo0tWApqHWmxKN35j6zUeI5R8yysl5R'], 
            'export_drive_table': ['']
            }

        qdict = QueryDict('', mutable=True)
        qdict.update(MultiValueDict(dictionary))

        fakeLink, fakeState = ("https://testworks.com", "testworks")
        fakeURI = 'https://flpinventory.com/report/'
        fakeCode = 'fakeCode'
    
        mock_build.return_value.files.return_value.create.return_value.execute.return_value = {
            'values': []}
        with patch.object(Flow, 'from_client_secrets_file') as patch_get_flow_obj:
            with patch.object(patch_get_flow_obj.return_value, 'authorization_url', return_value=(fakeLink, fakeState)) as patch_get_auth_url:
                response = self.client.post('/report/', qdict)
                patch_get_flow_obj.assert_called()
                patch_get_auth_url.assert_called()
                self.assertRedirects(response, fakeLink, fetch_redirect_response=False)
                self.assertEqual(patch_get_auth_url.return_value, (fakeLink, fakeState))
                self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
                self.assertEqual(response.status_code, 302)
                with patch.object(patch_get_flow_obj.return_value, 'fetch_token') as patch_fetch_token:
                    response = self.client.get('/report/', data={'code': fakeCode}, follow = True)

        # Check if valid
        self.assertEqual(patch_get_flow_obj.call_count, 2)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        patch_fetch_token.assert_called_with(code=fakeCode)
        mock_build.assert_called_with('drive', 'v3', credentials=patch_get_flow_obj.return_value.credentials)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/reports/generate_report.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['displaySuccessMessage'], True)
        self.assertEqual(response.context['tx_type'], 'Checkin')
        self.assertEqual(response.context['endDate'], today.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['startDate'], weekAgo.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['itemizedOutput'], 'itemized')

    @patch('inventory.gdrive.build')
    def test_export_drive_checkoutgbi_report(self, mock_build):
        self.client.login(username='testuser', password='12345')
        # Add item transaction
        session = self.client.session
        session['transactions-out'] = ['[{"model": "inventory.itemtransaction", "pk": null, "fields": {"item": 1, "quantity": 2}}]']
        session.save()

        response = self.client.post('/checkout/', data={"checkout": "", "family": "ValidFamily : (None)", "child": "Big Chungus", "age": "1"}, follow=True)

        # Check if valid
        self.assertEqual(response.status_code, 200)

        # Check if created
        self.assertEqual(Checkout.objects.filter().count(), 1)

        # Check for message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Checkout created.')

        today = date.today()
        weekAgo = today - timedelta(days=7)
        dictionary = {
            'tx-type': ['Checkout'],
            'start-date': [weekAgo.strftime('%Y-%m-%d')], 
            'end-date': [today.strftime('%Y-%m-%d')], 
            'itemizedOutput': ['itemized'],
            'csrfmiddlewaretoken': ['gorIARWkwGHd78mWsRPmvQIGcaE6FGtCxmo0tWApqHWmxKN35j6zUeI5R8yysl5R'], 
            'export_drive': ['']
            }

        qdict = QueryDict('', mutable=True)
        qdict.update(MultiValueDict(dictionary))

        fakeLink, fakeState = ("https://testworks.com", "testworks")
        fakeURI = 'https://flpinventory.com/report/'
        fakeCode = 'fakeCode'
    
        mock_build.return_value.files.return_value.create.return_value.execute.return_value = {
            'values': []}
        with patch.object(Flow, 'from_client_secrets_file') as patch_get_flow_obj:
            with patch.object(patch_get_flow_obj.return_value, 'authorization_url', return_value=(fakeLink, fakeState)) as patch_get_auth_url:
                response = self.client.post('/report/', qdict)
                patch_get_flow_obj.assert_called()
                patch_get_auth_url.assert_called()
                self.assertRedirects(response, fakeLink, fetch_redirect_response=False)
                self.assertEqual(patch_get_auth_url.return_value, (fakeLink, fakeState))
                self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
                self.assertEqual(response.status_code, 302)
                with patch.object(patch_get_flow_obj.return_value, 'fetch_token') as patch_fetch_token:
                    response = self.client.get('/report/', data={'code': fakeCode}, follow = True)

        # Check if valid
        self.assertEqual(patch_get_flow_obj.call_count, 2)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        patch_fetch_token.assert_called_with(code=fakeCode)
        mock_build.assert_called_with('drive', 'v3', credentials=patch_get_flow_obj.return_value.credentials)
        self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/reports/generate_report.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['displaySuccessMessage'], True)
        self.assertEqual(response.context['tx_type'], 'Checkout')
        self.assertEqual(response.context['endDate'], today.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['startDate'], weekAgo.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['itemizedOutput'], 'itemized')
    
    @patch('inventory.gdrive.build')
    def test_export_drive_error(self, mock_build):
        self.client.login(username='testuser', password='12345')
        # Add item transaction
        session = self.client.session
        session['transactions-out'] = ['[{"model": "inventory.itemtransaction", "pk": null, "fields": {"item": 1, "quantity": 2}}]']
        session.save()

        response = self.client.post('/checkout/', data={"checkout": "", "family": "ValidFamily : (None)", "child": "Big Chungus", "age": "1"}, follow=True)

        # Check if valid
        self.assertEqual(response.status_code, 200)

        # Check if created
        self.assertEqual(Checkout.objects.filter().count(), 1)

        # Check for message
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Checkout created.')

        today = date.today()
        weekAgo = today - timedelta(days=7)
        dictionary = {
            'tx-type': ['Checkout'],
            'start-date': [weekAgo.strftime('%Y-%m-%d')], 
            'end-date': [today.strftime('%Y-%m-%d')], 
            'itemizedOutput': ['itemized'],
            'csrfmiddlewaretoken': ['gorIARWkwGHd78mWsRPmvQIGcaE6FGtCxmo0tWApqHWmxKN35j6zUeI5R8yysl5R'], 
            'export_drive': ['']
            }

        qdict = QueryDict('', mutable=True)
        qdict.update(MultiValueDict(dictionary))

        fakeLink, fakeState = ("https://testworks.com", "testworks")
        fakeURI = 'https://flpinventory.com/report/'
        fakeError = 'fakeError'
    
        mock_build.return_value.files.return_value.create.return_value.execute.return_value = {
            'values': []}
        with patch.object(Flow, 'from_client_secrets_file') as patch_get_flow_obj:
            with patch.object(patch_get_flow_obj.return_value, 'authorization_url', return_value=(fakeLink, fakeState)) as patch_get_auth_url:
                response = self.client.post('/report/', qdict)
                patch_get_flow_obj.assert_called()
                patch_get_auth_url.assert_called()
                self.assertRedirects(response, fakeLink, fetch_redirect_response=False)
                self.assertEqual(patch_get_auth_url.return_value, (fakeLink, fakeState))
                self.assertEqual(patch_get_flow_obj.return_value.redirect_uri, fakeURI)
                self.assertEqual(response.status_code, 302)
                with patch.object(patch_get_flow_obj.return_value, 'fetch_token') as patch_fetch_token:
                    response = self.client.get('/report/', data={'error': fakeError}, follow = True)

        # Check if valid
        patch_get_flow_obj.assert_called_once()
        patch_fetch_token.assert_not_called()
        mock_build.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/reports/generate_report.html')
        self.assertEqual(len(response.context['results']), 1)
        self.assertEqual(response.context['displayErrorMessage'], True)
        self.assertEqual(response.context['tx_type'], 'Checkout')
        self.assertEqual(response.context['endDate'], today.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['startDate'], weekAgo.strftime('%Y-%m-%d'))
        self.assertEqual(response.context['itemizedOutput'], 'itemized')

from django.test import TestCase
from django.urls import reverse

from django_webtest import WebTest

from registration.models import Event, EventLink
from .forms import KumiteMatchPersonSwapForm
from .models import KumiteElim1Bracket, KumiteRoundRobinBracket, Kumite2PeopleBracket, KumiteMatchPerson, KumiteMatch
from .test_models import make_bracket
from accounts.models import RightsSupport

class KumiteMatchPersonSwapForm(TestCase):
    
    def test_run(self):
        
        self.client.force_login(RightsSupport.create_edit_user())
        
        #       a ---\___
        #  d --\_____/    \____
        #  e --/          /
        #       b ---\___/
        #       c ---/
        b = make_bracket(5)
        people = b.get_swappable_match_people()
        b2 = make_bracket(3)
        
        resp = self.client.get(b.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        form = resp.context['swap_form']
        
        # Swap with self
        url = reverse('kumite:bracket-n-swap', args=[b.id])
        resp = self.client.post(url, {'swap-src': people[0].id, 'swap-tgt': people[0].id})
        self.assertFormError(resp, 'swap_form', '', 'Can\'t swap with themselves.')
        
        # Person from another bracket
        other_p = b2.get_next_match().aka
        resp = self.client.post(url, {'swap-src': people[0].id, 'swap-tgt': other_p.id})
        self.assertFormError(resp, 'swap_form', 'tgt', 'Select a valid choice. That choice is not one of the available choices.')
        
        resp = self.client.post(url, {'swap-src': other_p.id, 'swap-tgt': people[0].id})
        self.assertFormError(resp, 'swap_form', 'src', 'Select a valid choice. That choice is not one of the available choices.')
        
        # Match done
        m = b.get_next_match()
        m.aka_won = True
        m.done = True
        m.save()
        resp = self.client.post(url, {'swap-src': m.aka.id, 'swap-tgt': m.shiro.id})
        self.assertFormError(resp, 'swap_form', 'src', 'Select a valid choice. That choice is not one of the available choices.')
        self.assertFormError(resp, 'swap_form', 'tgt', 'Select a valid choice. That choice is not one of the available choices.')
        
        # Valid swap
        #       c ---\___
        #  d --\_____/    \____
        #  e --/          /
        #       b ---\___/
        #       a ---/
        p1 = people.get(eventlink__manual_name="a")
        m1 = p1.kumitematch
        p2 = people.get(eventlink__manual_name="c")
        m2 = p2.kumitematch
        self.assertNotEqual(m1, m2)
        self.assertTrue(p1.is_aka())
        self.assertTrue(p2.is_shiro())
        resp = self.client.post(url, {'swap-src': p1.id, 'swap-tgt': p2.id})
        m1.refresh_from_db()
        m2.refresh_from_db()
        self.assertEqual(m1.aka, p2)
        self.assertEqual(m2.shiro, p1)
        self.assertRedirects(resp, b.get_absolute_url())
        
        # Test Get is rejected
        resp = self.client.get(url, {'swap-src': p1.id, 'swap-tgt': p2.id})
        self.assertEqual(resp.status_code, 405)
from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from .models import Rank

# Create your tests here.
class RankTestCase(TestCase):
    
    
    def test_get_kyu(self):
        rank = Rank.get_kyu(8)
        self.assertTrue(rank.name.startswith("Yellow"))
        
        with self.assertRaises(ObjectDoesNotExist):
            rank = Rank.get_kyu(10)
    
    
    def test_get_dan(self):
        rank = Rank.get_dan(2)
        self.assertTrue(rank.name.startswith("Nidan"))
    
        with self.assertRaises(ObjectDoesNotExist):
            rank = Rank.get_dan(0)
    
    
    def test_build_default_fixture(self):
        """Check that default entries have been populated.
        
        The rank fixture should have been automatically loaded by DB migration.
        Check that it is populated and that it matches the generation function 
        and the saved fixture.
        """
        
        from django.core import serializers
        import os
        import io
        
        db = serializers.serialize("json", Rank.objects.all(), indent=4)
        
        filename = os.path.realpath(__file__)
        filename = os.path.join(os.path.dirname(filename), "fixtures", "rank.json")
        with open(filename) as f:
            filename = f.read()
        
        fun = io.StringIO()
        Rank.build_default_fixture(fun)
        fun.seek(0)
        fun = fun.read()
        
        self.assertJSONEqual(db, filename)
        self.assertJSONEqual(db, fun)

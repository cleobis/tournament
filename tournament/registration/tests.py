from django.test import TestCase

from .models import Rank

# Create your tests here.
class RankTestCase(TestCase):
    
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
        # print(db)
        db = io.StringIO(db)
        
        filename = os.path.realpath(__file__)
        filename = os.path.join(os.path.dirname(filename), "fixtures", "rank.json")
        
        fun = io.StringIO()
        Rank.build_default_fixture(fun)
        fun.seek(0)
        
        with open(filename) as f:
            line = 1
            line_db = "start"
            line_file = "start"
            line_fun = "start"
            while len(line_db) > 0 or len(line_file) > 0:
                line_db = db.readline()
                line_file = f.readline()
                line_fun = fun.readline()
                self.assertEquals(line_db.strip(), line_file.strip(), "Error on line {}.".format(line))
                self.assertEquals(line_file, line_fun, "Error on line {}.".format(line))
                line += 1
        
        # XMLSerializer = serializers.get_serializer("json")
        # xml_serializer = XMLSerializer()
        # xml_serializer.serialize(Rank.objects.all())
        # data = xml_serializer.getvalue()
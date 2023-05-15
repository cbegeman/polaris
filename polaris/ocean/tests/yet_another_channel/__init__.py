from polaris import TestGroup
from polaris.ocean.tests.yet_another_channel.default import Default


class YetAnotherChannel(TestGroup):
    """
    A test group for "yet another channel" test cases
    """
    def __init__(self, component):
        """
        component : polaris.ocean.Ocean
            the ocean component that this test group belongs to
        """
        super().__init__(component=component, name='yet_another_channel')

        self.add_test_case(
            Default(test_group=self))

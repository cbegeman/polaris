from polaris import TestCase


class Default(TestCase):
    """
    The default test case for the "yet another channel" test group simply
    creates the mesh and initial condition, then performs a short forward
    run on 4 cores.
    """

    def __init__(self, test_group):
        """
        Create the test case

        Parameters
        ----------
        test_group : polaris.ocean.tests.yet_another_channel.YetAnotherChannel
            The test group that this test case belongs to
        """
        name = 'default'
        super().__init__(test_group=test_group, name=name)

class PairedOrganization:
    """
    Combines an organization's name "UCSD" with its marker "CAL_PMC_UCSD".
    """

    def __init__(self, _organization: str, _marker: str):
        """
        Links an organization's name with its marker.
        """

        self.organization = _organization
        self.marker = _marker

import xml.etree.ElementTree as ET
import re
import requests


class Evaluator(object):
    """
    A class used to define FAIR indicators tests

    ...

    Attributes
    ----------
    item_id : str
        Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

    """

    def __init__(self, item_id):
        self.item_id = item_id

    # TESTS
    #    FINDABLE

    def rda_f1_01m(self):
        """ Indicator RDA-F1-01M
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the metadata is identified by a persistent identifier.
        A persistent identifier ensures that the metadata will remain findable over time, and reduces
        the risk of broken links.

        Technical proposal:Depending on the type od item_id, defined, it should check if it is any of
        the allowed Persistent Identifiers (DOI, PID) to identify digital objects.

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_f1_01d(self):
        """ Indicator RDA-F1-01D
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        This indicator evaluates whether or not the data is identified by a persistent identifier. A
        persistent identifier ensures that the data will remain findable over time, and reduces the
        risk of broken links.

        Technical proposal: If the repository/system where the digital object is stored has both data
        and metadata integrated, this method only need to call the previous one. Otherwise, it needs
        to be re-defined.

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg = self.rda_f1_01m()
        return points, msg

    def rda_f1_02m(self):
        """ Indicator RDA-F1-02M
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        The indicator serves to evaluate whether the identifier of the metadata is globally unique,
        i.e. that there are no two identical identifiers that identify different metadata records.

        Technical proposal: It should check not only if the persistent identifier exists, but also
        if it can be resolved and if it is minted by any authorizated organization (e.g. DataCite)

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 0
        msg = "Test has not been performed correctly"
        print("Type of doi %s" % type(self.item_id))
        id_to_check = self.get_doi_str(self.item_id)
        print("ID to check: ")
        print(id_to_check)
        if len(id_to_check) != 0:
            if self.check_doi(id_to_check):
                points = 100
                msg = "Your Unique identifier is a correct DOI"
        id_to_check = self.get_handle_str(self.item_id)
        if len(id_to_check) != 0:
            if self.check_handle(id_to_check):
                points = 100
                msg = "Your Unique identifier is a correct Handle PID"
        else:
            points = 0
            msg = "Persistent Identifier has not been classified among the registered (DOI, Handle)"

        return points, msg

    def rda_f1_02d(self):
        """ Indicator RDA-F1-02D
        This indicator is linked to the following principle: F1 (meta)data are assigned a globally
        unique and eternally persistent identifier. More information about that principle can be found
        here.

        The indicator serves to evaluate whether the identifier of the data is globally unique, i.e.
        that there are no two people that would use that same identifier for two different digital
        objects.

        Technical proposal:  If the repository/system where the digital object is stored has both data
        and metadata integrated, this method only need to call the previous one. Otherwise, it needs
        to be re-defined.

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        return self.rda_f1_02m()

    def rda_f2_01m(self):
        """ Indicator RDA-F2-01M
        This indicator is linked to the following principle: F2: Data are described with rich metadata.

        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.

        Technical proposal: Two different tests to evaluate generic and disciplinar metadata if needed.


        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points_g, msg_g = self.rda_f2_01m_generic()
        points_d, msg_d = self.rda_f2_01m_disciplinar()
        return (points_g + points_d) / 2, msg_g + " | " + msg_d

    def rda_f2_01m_generic(self):
        """ Indicator RDA-F2-01M_GENERIC
        This indicator is linked to the following principle: F2: Data are described with rich metadata.

        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.

        Technical proposal: Check if all the dublin core terms are OK

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_f2_01m_disciplinar(self):
        """ Indicator RDA-F2-01M_DISCIPLINAR
        This indicator is linked to the following principle: F2: Data are described with rich metadata.

        The indicator is about the presence of metadata, but also about how much metadata is
        provided and how well the provided metadata supports discovery.

        Technical proposal: This test should be more complex

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_f3_01m(self):
        """ Indicator RDA-F3-01M
        This indicator is linked to the following principle: F3: Metadata clearly and explicitly include
        the identifier of the data they describe. More information about that principle can be found
        here.

        The indicator deals with the inclusion of the reference (i.e. the identifier) of the digital object
        in the metadata so that the digital object can be accessed.

        Technical proposal: Check the metadata term where the object is identified

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_f4_01m(self):
        """ Indicator RDA-F4-01M
        This indicator is linked to the following principle: F4: (Meta)data are registered or indexed
        in a searchable resource. More information about that principle can be found here.

        The indicator tests whether the metadata is offered in such a way that it can be indexed.
        In some cases, metadata could be provided together with the data to a local institutional
        repository or to a domain-specific or regional portal, or metadata could be included in a
        landing page where it can be harvested by a search engine. The indicator remains broad
        enough on purpose not to  limit the way how and by whom the harvesting and indexing of
        the data might be done.

        Technical proposal: Check some standard harvester like OAI-PMH

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    #  ACCESSIBLE

    def rda_a1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator refers to the information that is necessary to allow the requester to gain access
        to the digital object. It is (i) about whether there are restrictions to access the data (i.e.
        access to the data may be open, restricted or closed), (ii) the actions to be taken by a
        person who is interested to access the data, in particular when the data has not been
        published on the Web and (iii) specifications that the resources are available through
        eduGAIN7 or through specialised solutions such as proposed for EPOS.

        Technical proposal: Resolve the identifier

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_02m(self):
        """ Indicator RDA-A1-02M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        The indicator refers to any human interactions that are needed if the requester wants to
        access metadata. The FAIR principle refers mostly to automated interactions where a
        machine is able to access the metadata, but there may also be metadata that require human
        interactions. This may be important in cases where the metadata itself contains sensitive
        information. Human interaction might involve sending an e-mail to the metadata owner, or
        calling by telephone to receive instructions.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_02d(self):
        """ Indicator RDA-A1-02D
        This indicator is linked to the following principle: A1: (Meta)data are retrievable
        by their identifier using a standardised communication protocol.

        The indicator refers to any human interactions that are needed if the requester
        wants to access the digital object. The FAIR principle refers mostly to
        automated interactions where a machine is able to access the digital object, but
        there may also be digital objects that require human interactions, such as
        clicking on a link on a landing page, sending an e-mail to the data owner, or
        even calling by telephone.

        The indicator can be evaluated by looking for information in the metadata that
        describes how access to the digital object can be obtained through human
        intervention.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_03m(self):
        """ Indicator RDA-A1-03M Metadata identifier resolves to a metadata record
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol.

        This indicator is about the resolution of the metadata identifier. The identifier assigned to
        the metadata should be associated with a resolution service that enables access to the
        metadata record.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg = self.rda_f1_02m()
        return points, msg

    def rda_a1_03d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        This indicator is about the resolution of the identifier that identifies the digital object. The
        identifier assigned to the data should be associated with a formally defined
        retrieval/resolution mechanism that enables access to the digital object, or provides access
        instructions for access in the case of human-mediated access. The FAIR principle and this
        indicator do not say anything about the mutability or immutability of the digital object that
        is identified by the data identifier -- this is an aspect that should be governed by a
        persistence policy of the data provider

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points, msg = self.rda_a1_03m()
        return points, msg

    def rda_a1_04m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator concerns the protocol through which the metadata is accessed and requires
        the protocol to be defined in a standard.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_04d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator concerns the protocol through which the digital object is accessed and requires
        the protocol to be defined in a standard.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_05d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1: (Meta)data are retrievable by their
        identifier using a standardised communication protocol. More information about that
        principle can be found here.

        The indicator refers to automated interactions between machines to access digital objects.
        The way machines interact and grant access to the digital object will be evaluated by the
        indicator.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator tests that the protocol that enables the requester to access metadata can be
        freely used. Such free use of the protocol enhances data reusability.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_1_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.1: The protocol is open, free and
        universally implementable. More information about that principle can be found here.

        The indicator requires that the protocol can be used free of charge which facilitates
        unfettered access.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a1_2_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A1.2: The protocol allows for an
        authentication and authorisation where necessary. More information about that principle
        can be found here.

        The indicator requires the way that access to the digital object can be authenticated and
        authorised and that data accessibility is specifically described and adequately documented.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_a2_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: A2: Metadata should be accessible even
        when the data is no longer available. More information about that principle can be found
        here.

        The indicator intends to verify that information about a digital object is still available after
        the object has been deleted or otherwise has been lost. If possible, the metadata that
        remains available should also indicate why the object is no longer available.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    # INTEROPERABLE

    def rda_i1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        The indicator serves to determine that an appropriate standard is used to express
        knowledge, for example, controlled vocabularies for subject classifications.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i1_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        The indicator serves to determine that an appropriate standard is used to express
        knowledge, in particular the data model and format.

        Technical proposal: Data format is within a list of accepted standards.

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i1_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the metadata. This means
        that metadata should be readable and thus interoperable for machines without any
        requirements such as specific translators or mappings.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i1_02d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I1: (Meta)data use a formal, accessible,
        shared, and broadly applicable language for knowledge representation. More information
        about that principle can be found here.

        This indicator focuses on the machine-understandability aspect of the data. This means that
        data should be readable and thus interoperable for machines without any requirements such
        as specific translators or mappings.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i2_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.

        The indicator requires the vocabulary used for the metadata to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique and persistent
        identifiers. The documentation needs to be easily findable and accessible.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i2_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I2: (Meta)data use vocabularies that follow
        the FAIR principles. More information about that principle can be found here.

        The indicator requires the controlled vocabulary used for the data to conform to the FAIR
        principles, and at least be documented and resolvable using globally unique
        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i3_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        The indicator is about the way that metadata is connected to other metadata, for example
        through links to information about organisations, people, places, projects or time periods
        that are related to the digital object that the metadata describes.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i3_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way data is connected to other data, for example linking to
        previous or related research data that provides additional context to the data.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i3_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other data, for example linking to
        previous or related research data that provides additional context to the data. Please note
        that this is not about the link from the metadata to the data it describes; that link is
        considered in principle F3 and in indicator RDA-F3-01M.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
    """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i3_02d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.
        Description of the indicator RDA-I3-02D

        This indicator is about the way data is connected to other data. The references need to be
        qualified which means that the relationship role of the related resource is specified, for
        example that a particular link is a specification of a unit of m

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i3_03m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other metadata, for example to
        descriptions of related resources that provide additional context to the data. The references
        need to be qualified which means that the relation

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_i3_04m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: I3: (Meta)data include qualified references
        to other (meta)data. More information about that principle can be found here.

        This indicator is about the way metadata is connected to other data. The references need
        to be qualified which means that the relationship role of the related resource is specified,
        for example dataset X is derived from dataset Y.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    # REUSABLE

    def rda_r1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1: (Meta)data are richly described with a
        plurality of accurate and relevant attributes. More information about that principle can be
        found here.

        The indicator concerns the quantity but also the quality of metadata provided in order to
        enhance data reusability.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_1_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license.

        This indicator is about the information that is provided in the metadata related to the
        conditions (e.g. obligations, restrictions) under which data can be reused.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_1_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license.

        This indicator requires the reference to the conditions of reuse to be a standard licence,
        rather than a locally defined licence.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_1_03m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.1: (Meta)data are released with a clear
        and accessible data usage license. More information about that principle can be found here.

        This indicator is about the way that the reuse licence is expressed. Rather than being a
        human-readable text, the licence should be expressed in such a way that it can be processed
        by machines, without human intervention, for example in automated searches.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_2_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.2: (Meta)data are associated with
        detailed provenance. More information about that principle can be found here.

        This indicator requires the metadata to include information about the provenance of the
        data, i.e. information about the origin, history or workflow that generated the data, in a
        way that is compliant with the standards that are used in the community in which the data
        is produced.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_2_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.2: (Meta)data are associated with
        detailed provenance. More information about that principle can be found here.

        This indicator requires that the metadata provides provenance information according to a
        cross-domain language.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_3_01m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that metadata complies with community standards.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_3_01d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.

        This indicator requires that data complies with community standards.
        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_3_02m(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards. More information about that principle can be found here.

        This indicator requires that the metadata follows a community standard that has a machineunderstandable expression.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    def rda_r1_3_02d(self):
        """ Indicator RDA-A1-01M
        This indicator is linked to the following principle: R1.3: (Meta)data meet domain-relevant
        community standards.

        This indicator requires that the data follows a community standard that has a machineunderstandable expression.

        Technical proposal:

        Parameters
        ----------
        item_id : str
            Digital Object identifier, which can be a generic one (DOI, PID), or an internal (e.g. an
            identifier from the repo)

        Returns
        -------
        points
            A number between 0 and 100 to indicate how well this indicator is supported
        msg
            Message with the results or recommendations to improve this indicator
        """
        points = 50
        msg = "Test not implemented"
        return points, msg

    # UTILS
    def get_doi_str(self, doi_str):
        doi_to_check = re.findall(
            r'10[\.-]+.[\d\.-]+/[\w\.-]+[\w\.-]+/[\w\.-]+[\w\.-]', doi_str)
        if len(doi_to_check) == 0:
            doi_to_check = re.findall(
                r'10[\.-]+.[\d\.-]+/[\w\.-]+[\w\.-]', doi_str)
        if len(doi_to_check) != 0:
            return doi_to_check[0]
        else:
            return ''

    def get_handle_str(self, pid_str):
        handle_to_check = re.findall(r'[\d\.-]+/[\w\.-]+[\w\.-]', pid_str)
        if len(handle_to_check) != 0:
            return handle_to_check[0]
        else:
            return ''

    def get_orcid_str(self, orcid_str):
        orcid_to_check = re.findall(
            r'[\d\.-]+-[\w\.-]+-[\w\.-]+-[\w\.-]', orcid_str)
        if len(orcid_to_check) != 0:
            return orcid_to_check[0]
        else:
            return ''

    def check_doi(self, doi):
        url = "http://dx.doi.org/%s" % str(doi)  # DOI solver URL
        # Type of response accpeted
        headers = {'Accept': 'application/vnd.citationstyles.csl+json;q=1.0'}
        r = requests.post(url, headers=headers)  # POST with headers
        print(r.status_code)
        if r.status_code == 200:
            return True
        else:
            return False

    def check_handle(self, pid):
        handle_base_url = "http://hdl.handle.net/"
        return self.check_url(handle_base_url + pid)

    def check_orcid(self, orcid):
        orcid_base_url = "https://orcid.org/"
        return self.check_url(orcid_base_url + orcid)

    def check_url(self, url):
        try:
            resp = False
            r = requests.get(url, verify=False)  # Get URL
            print(url)
            if r.status_code == 200:
                resp = True
            else:
                resp = False
        except Exception as err:
            resp = False
            print("Error: %s" % err)
        return resp

    def check_oai_pmh_item(self, base_url, identifier):
        try:
            resp = False
            url = "%s?verb=GetRecord&metadataPrefix=oai_dc&identifier=%s" % (
                base_url, identifier)
            print("OAI-PMH URL: %s" % url)
            r = requests.get(url, verify=False)  # Get URL
            xmlTree = ET.fromstring(r.text)
            resp = True
        except Exception as err:
            resp = False
            print("Error: %s" % err)
        return resp

    def get_color(self, points):
        color = "#F4D03F"
        if points < 50:
            color = "#E74C3C"
        elif points > 80:
            color = "#2ECC71"
        return color


def oai_identify(oai_base):
    action = "?verb=Identify"
    print("Request to: %s%s" % (oai_base, action))
    return oai_request(oai_base, action)


def oai_metadataFormats(oai_base):
    action = '?verb=ListMetadataFormats'
    print("Request to: %s%s" % (oai_base, action))
    xmlTree = oai_request(oai_base, action)
    metadataFormats = {}
    for e in xmlTree.findall('.//{http://www.openarchives.org/OAI/2.0/}metadataFormat'):
        metadataPrefix = e.find('{http://www.openarchives.org/OAI/2.0/}metadataPrefix').text
        namespace = e.find('{http://www.openarchives.org/OAI/2.0/}metadataNamespace').text
        metadataFormats[metadataPrefix] = namespace
        print(metadataPrefix, ':', namespace)
    return metadataFormats


def oai_check_record_url(oai_base, metadata_prefix, pid):
    endpoint_root = urllib.parse.urlparse(oai_base).netloc
    pid_type = idutils.detect_identifier_schemes(pid)[0]
    oai_pid = idutils.normalize_pid(pid, pid_type)
    action = "?verb=GetRecord"
    
    test_id = "oai:%s:%s" % (endpoint_root, oai_pid)
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)
    url_final = ''
    url = oai_base + action + params
    print("Trying: " + url)
    response = requests.get(url)
    print("Error?")
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        print(tags.text)
        error = error + 1
    if error == 0:
        url_final = url
    
    
    test_id = "%s:%s" % (pid_type, oai_pid)
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)
    
    url = oai_base + action + params
    print("Trying: " + url)
    response = requests.get(url)
    print("Error?")
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        print(tags)
        error = error + 1
    if error == 0:
        url_final = url
    
    test_id = "oai:%s:%s" % (endpoint_root, oai_pid[oai_pid.rfind(".")+1:len(oai_pid)])
    params = "&metadataPrefix=%s&identifier=%s" % (metadata_prefix, test_id)
    
    url = oai_base + action + params
    print("Trying: " + url)
    response = requests.get(url)
    print("Error?")
    error = 0
    for tags in ET.fromstring(response.text).findall('.//{http://www.openarchives.org/OAI/2.0/}error'):
        print(tags)
        error = error + 1
    if error == 0:
        url_final = url
    
    return url_final


def oai_get_metadata(url):
    oai = requests.get(url)
    xmlTree = ET.fromstring(oai.text)
    return xmlTree


def oai_request(oai_base, action):
    oai = requests.get(oai_base + action) #Peticion al servidor
    xmlTree = ET.fromstring(oai.text)
    return xmlTree

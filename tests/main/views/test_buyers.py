# coding: utf-8
from __future__ import unicode_literals

from ...helpers import BaseApplicationTest
from dmapiclient import api_stubs, HTTPError
from dmcontent.content_loader import ContentLoader
from dmcontent.questions import Question
import mock
from lxml import html
import pytest

from app.main.views import buyers
from dmapiclient import DataAPIClient
from freezegun import freeze_time
import functools
import inflection
import sys

from werkzeug.exceptions import NotFound


po = functools.partial(mock.patch.object, autospec=True)


@pytest.fixture()
def find_briefs_mock():
    base_brief_values = {
        "createdAt": "2016-02-01T00:00:00.000000Z",
        "frameworkSlug": "digital-outcomes-and-specialists-2",
        "frameworkFramework": "digital-outcomes-and-specialists",
        "lot": "digital-specialists"
    }

    find_briefs_response = {
        "briefs": [
            {
                "id": 20,
                "status": "draft",
                "title": "A draft brief"
            },
            {
                "id": 21,
                "status": "live",
                "title": "A live brief",
                "publishedAt": "2016-02-04T12:00:00.000000Z"
            },
            {
                "id": 22,
                "status": "closed",
                "title": "A closed brief with brief responses",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-18T12:00:00.000000Z"
            },
            {
                "id": 23,
                "status": "withdrawn",
                "title": "A withdrawn brief",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "withdrawnAt": "2016-02-05T12:00:00.000000Z"
            },
            {
                "id": 24,
                "status": "awarded",
                "title": "An awarded brief",
                "publishedAt": "2016-02-03T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-19T12:00:00.000000Z"

            },
            {
                "id": 25,
                "status": "closed",
                "title": "A closed brief with no brief responses",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-18T12:00:00.000000Z"
            },
            {
                "id": 26,
                "status": "cancelled",
                "title": "A cancelled brief",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-17T12:00:00.000000Z"
            },
            {
                "id": 27,
                "status": "unsuccessful",
                "title": "An unsuccessful brief where no suitable suppliers applied",
                "publishedAt": "2016-02-04T12:00:00.000000Z",
                "applicationsClosedAt": "2016-02-16T12:00:00.000000Z"
            },
        ]
    }

    for brief in find_briefs_response['briefs']:
        brief.update(base_brief_values)

    return find_briefs_response


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestBuyerDashboard(BaseApplicationTest):

    def setup_method(self, method):
        super(TestBuyerDashboard, self).setup_method(method)
        self.login_as_buyer()

    def test_draft_briefs_section(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')

        assert res.status_code == 200

        draft_row = [cell.text_content().strip() for cell in tables[0].xpath('.//tbody/tr/td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/20'

        assert draft_row[0] == "A draft brief"
        assert tables[0].xpath('.//tbody/tr')[0].xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert draft_row[1] == "Monday 1 February 2016"

    def test_live_briefs_section(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')

        assert res.status_code == 200

        live_row = [cell.text_content().strip() for cell in tables[1].xpath('.//tbody/tr/td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/21'

        assert live_row[0] == "A live brief"
        assert tables[1].xpath('.//tbody/tr')[0].xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert live_row[1] == "Thursday 4 February 2016"

    def test_closed_briefs_section_with_closed_brief(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        closed_row_cells = tables[2].xpath('.//tbody/tr')[0].xpath('.//td')

        assert closed_row_cells[0].xpath('.//a')[0].text_content() == "A closed brief with brief responses"
        assert closed_row_cells[0].xpath('.//a/@href')[0] == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/22'

        assert tables[2].xpath('.//tbody/tr/td')[1].text_content().strip() == "Thursday 18 February 2016"

        assert closed_row_cells[2].xpath('.//a')[0].text_content() == "View responses"
        assert closed_row_cells[2].xpath('.//a/@href')[0] == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/22/responses'

        assert closed_row_cells[2].xpath('.//a')[1].text_content() == "Tell us who won this contract"
        assert closed_row_cells[2].xpath('.//a/@href')[1] == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/22/award-contract'

    def test_closed_briefs_section_with_withdrawn_brief(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        withdrawn_row = tables[2].xpath('.//tbody/tr')[1]
        withdrawn_row_cells = [cell.text_content().strip() for cell in withdrawn_row.xpath('.//td')]
        expected_link = '/digital-outcomes-and-specialists/opportunities/23'

        assert withdrawn_row_cells[0] == "A withdrawn brief"
        assert withdrawn_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert withdrawn_row_cells[1] == "Withdrawn"
        assert "View responses" not in withdrawn_row_cells[2]
        assert "Tell us who won this contract" not in withdrawn_row_cells[2]

    def test_closed_briefs_section_with_awarded_brief(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        awarded_row = tables[2].xpath('.//tbody/tr')[2]
        awarded_row_cells = [cell.text_content().strip() for cell in awarded_row.xpath('.//td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/24'

        assert awarded_row_cells[0] == "An awarded brief"
        assert awarded_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert awarded_row_cells[1] == "Friday 19 February 2016"
        assert "View responses" not in awarded_row_cells[2]
        assert "Tell us who won this contract" not in awarded_row_cells[2]

    def test_closed_briefs_section_with_cancelled_brief(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        cancelled_row = tables[2].xpath('.//tbody/tr')[4]
        cancelled_row_cells = [cell.text_content().strip() for cell in cancelled_row.xpath('.//td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/26'

        assert cancelled_row_cells[0] == "A cancelled brief"
        assert cancelled_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert cancelled_row_cells[1] == "Wednesday 17 February 2016"
        assert "View responses" not in cancelled_row_cells[2]
        assert "Tell us who won this contract" not in cancelled_row_cells[2]

    def test_closed_briefs_section_with_unsuccessful_brief(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        res = self.client.get("/buyers")

        assert res.status_code == 200
        tables = html.fromstring(res.get_data(as_text=True)).xpath('//table')
        unsuccessful_row = tables[2].xpath('.//tbody/tr')[5]
        unsuccessful_row_cells = [cell.text_content().strip() for cell in unsuccessful_row.xpath('.//td')]
        expected_link = '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/27'

        assert unsuccessful_row_cells[0] == "An unsuccessful brief where no suitable suppliers applied"
        assert unsuccessful_row.xpath('.//td')[0].xpath('.//a/@href')[0] == expected_link
        assert unsuccessful_row_cells[1] == "Tuesday 16 February 2016"
        assert "View responses" not in unsuccessful_row_cells[2]
        assert "Tell us who won this contract" not in unsuccessful_row_cells[2]

    def test_flash_message_shown_if_brief_has_just_been_updated(self, data_api_client, find_briefs_mock):
        data_api_client.find_briefs.return_value = find_briefs_mock

        with self.client.session_transaction() as session:
            session['_flashes'] = [
                ('message', {'updated-brief': "My Amazing Brief"})
            ]

        res = self.client.get("/buyers")

        flash_div = html.fromstring(res.get_data(as_text=True)).xpath('//div[@class="banner-success-without-action"]')
        assert flash_div[0].text_content().strip() == "You've updated 'My Amazing Brief'"


class TestBuyerRoleRequired(BaseApplicationTest):
    def test_login_required_for_buyer_pages(self):
        with self.app.app_context():
            res = self.client.get('/buyers')
            assert res.status_code == 302
            assert res.location == 'http://localhost/user/login?next=%2Fbuyers'

    def test_supplier_cannot_access_buyer_pages(self):
        with self.app.app_context():
            self.login_as_supplier()
            res = self.client.get('/buyers')
            assert res.status_code == 302
            assert res.location == 'http://localhost/user/login?next=%2Fbuyers'
            self.assert_flashes('buyer-role-required', expected_category='error')

    @mock.patch('app.main.views.buyers.data_api_client')
    def test_buyer_pages_ok_if_logged_in_as_buyer(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.get('/buyers')
            page_text = res.get_data(as_text=True)

            assert res.status_code == 200
            assert 'buyer@email.com' in page_text
            assert u'Ā Buyer' in page_text


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestStartNewBrief(BaseApplicationTest):
    def test_show_start_brief_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

            assert res.status_code == 200

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False)
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

            assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            with self.app.app_context():
                self.login_as_buyer()
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create")

                assert res.status_code == 404

    def test_404_if_lot_does_not_exist(self, data_api_client):
        with self.app.app_context():
            with self.app.app_context():
                self.login_as_buyer()
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status='live',
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses/create")

                assert res.status_code == 404


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestCreateNewBrief(BaseApplicationTest):
    def test_create_new_digital_specialists_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": "Title"
            })

        assert res.status_code == 302
        data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )

    def test_create_new_digital_outcomes_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/create",
            data={
                "title": "Title"
            })

        assert res.status_code == 302
        data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-outcomes',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "specialistRole": "agileCoach"
            })

        assert res.status_code == 404
        assert not data_api_client.create_brief.called

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "specialistRole": "agileCoach"
            })

        assert res.status_code == 404
        assert not data_api_client.create_brief.called

    def test_404_if_lot_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='open',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses/create",
            data={
                "specialistRole": "agileCoach"
            })

        assert res.status_code == 404
        assert not data_api_client.create_brief.called

    def test_400_if_form_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.create_brief.side_effect = HTTPError(
            mock.Mock(status_code=400),
            {"title": "answer_required"})

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/create",
            data={
                "title": "Title"
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        anchor = document.cssselect('div.validation-masthead a[href="#title"]')

        assert len(anchor) == 1
        assert "Title" in anchor[0].text_content().strip()
        data_api_client.create_brief.assert_called_with(
            'digital-outcomes-and-specialists',
            'digital-specialists',
            123,
            {'title': "Title"},
            page_questions=['title'],
            updated_by='buyer@email.com'
        )


class TestCopyBrief(BaseApplicationTest):

    def setup_method(self, method):
        super(TestCopyBrief, self).setup_method(method)
        self.login_as_buyer()
        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.brief = api_stubs.brief(
            framework_slug="digital-outcomes-and-specialists-2",
            framework_name="Digital Outcomes and Specialists 2"
        )
        self.data_api_client.get_brief.return_value = self.brief

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super(TestCopyBrief, self).teardown_method(method)

    def test_get_not_allowed(self):
        res = self.client.get(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        assert res.status_code == 404

    def test_copy_brief_and_redirect_to_copied_brief_edit_title_page(self):
        new_brief = self.brief.copy()
        new_brief["briefs"]["id"] = 1235
        self.data_api_client.copy_brief.return_value = new_brief

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        self.data_api_client.copy_brief.assert_called_once_with('1234', 'buyer@email.com')

        assert res.location == (
            "http://localhost/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/"
            "1235/edit/title/title"
        )

    def test_copy_brief_for_expired_framework_redirects_to_edit_page_for_new_framework(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief()  # dos1 brief

        new_brief = self.brief.copy()  # dos2 brief
        new_brief["briefs"]["id"] = 1235
        self.data_api_client.copy_brief.return_value = new_brief

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/copy'
        )

        assert res.location == (
            "http://localhost/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/"
            "1235/edit/title/title"
        )

    @mock.patch("app.main.views.buyers.is_brief_correct", autospec=True)
    def test_404_if_brief_is_not_correct(self, is_brief_correct):
        is_brief_correct.return_value = False

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        assert res.status_code == 404
        is_brief_correct.assert_called_once_with(
            self.brief["briefs"],
            "digital-outcomes-and-specialists-2",
            "digital-specialists",
            123,
            allow_withdrawn=True
        )

    def test_can_copy_withdrawn_brief(self):
        # Make our original brief withdrawn
        withdrawn_brief = self.brief.copy()
        withdrawn_brief["briefs"].update({'status': 'withdrawn'})
        self.data_api_client.get_brief.return_value = withdrawn_brief

        # Set copied brief return
        new_brief = self.brief.copy()  # dos2 brief
        new_brief["briefs"]["id"] = 1235
        self.data_api_client.copy_brief.return_value = new_brief

        res = self.client.post(
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234/copy'
        )

        # Assert redirect and copy_brief call
        assert res.status_code == 302
        self.data_api_client.copy_brief.assert_called_once_with('1234', 'buyer@email.com')


class TestEveryDamnPage(BaseApplicationTest):
    def _load_page(self, url, status_code, method='get', data=None, framework_status='live', brief_status='draft'):
        data = {} if data is None else data
        baseurl = "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
        with mock.patch('app.main.views.buyers.content_loader', autospec=True) as content_loader, \
                mock.patch('app.main.views.buyers.data_api_client', autospec=True) as data_api_client:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    api_stubs.lot(slug='digital-outcomes', allows_brief=True)
                ]
            )
            brief_stub = api_stubs.brief()
            brief_stub['briefs'].update({'status': brief_status})
            if brief_status != 'draft':
                brief_stub['briefs'].update({'publishedAt': '2017-01-21T12:00:00.000000Z'})
            data_api_client.get_brief.return_value = brief_stub

            content_fixture = ContentLoader('tests/fixtures/content')
            content_fixture.load_manifest('dos', 'data', 'edit_brief')
            content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

            res = getattr(self.client, method)(
                "{}{}".format(baseurl, url),
                data=data)
            assert res.status_code == status_code

    # These should all work as expected

    def test_get_view_brief_overview(self):
        for framework_status in ['live', 'expired']:
            self._load_page("/digital-specialists/1234", 200, framework_status=framework_status)

    def test_get_view_section_summary(self):
        self._load_page("/digital-specialists/1234/section-1", 200)

    def test_get_edit_brief_question(self):
        self._load_page("/digital-specialists/1234/edit/section-1/required1", 200)

    def test_post_edit_brief_question(self):
        data = {"required1": True}
        self._load_page("/digital-specialists/1234/edit/section-1/required1", 302, method='post', data=data)

    def test_get_view_brief_responses(self):
        for framework_status in ['live', 'expired']:
            self._load_page("/digital-specialists/1234/responses", 200, brief_status='closed')

    # get and post are the same for publishing

    def test_post_delete_a_brief(self):
        data = {"delete_confirmed": True}
        self._load_page("/digital-specialists/1234/delete", 302, method='post', data=data)

    # Wrong lots

    def test_wrong_lot_get_view_brief_overview(self):
        self._load_page("/digital-outcomes/1234", 404)

    def test_wrong_lot_get_view_section_summary(self):
        self._load_page("/digital-outcomes/1234/section-1", 404)

    def test_wrong_lot_get_edit_brief_question(self):
        self._load_page("/digital-outcomes/1234/edit/section-1/required1", 404)

    def test_wrong_lot_post_edit_brief_question(self):
        data = {"required1": True}
        self._load_page("/digital-outcomes/1234/edit/section-1/required1", 404, method='post', data=data)

    def test_wrong_lot_get_view_brief_responses(self):
        self._load_page("/digital-outcomes/1234/responses", 404)

    # get and post are the same for publishing
    def test_wrong_lot_publish_brief(self):
        self._load_page("/digital-outcomes/1234/publish", 404)

    def test_wrong_lot_post_delete_a_brief(self):
        data = {"delete_confirmed": True}
        self._load_page("/digital-outcomes/1234/delete", 404, method='post', data=data)

    # not allowed for expired framework_slug

    def test_expired_framework_get_edit_brief_question(self):
        self._load_page("/digital-specialists/1234/edit/section-1/required1", 404, framework_status='expired')

    def test_expired_framework_post_edit_brief_question(self):
        data = {"required1": True}
        self._load_page(
            "/digital-outcomes/1234/edit/section-1/required1",
            404,
            method='post',
            data=data,
            framework_status='expired'
        )

    @pytest.mark.parametrize("lot_slug", ('digital-outcomes', 'digital-specialists'))
    def test_expired_framework_post_edit_brief_question(self, lot_slug):
        data = {"required1": True}
        self._load_page(
            "/{}/1234/edit/section-1/required1".format(lot_slug),
            404,
            method='post',
            data=data,
            framework_status='expired'
        )


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestEditBriefSubmission(BaseApplicationTest):

    def _test_breadcrumbs_on_question_page(self, response, has_summary_page=False, section_name=None):
        extra_breadcrumbs = [
            ('I need a thing to do a thing',
             '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234')
        ]
        if has_summary_page and section_name:
            extra_breadcrumbs.append((
                section_name,
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/{}'.format(
                    section_name.lower().replace(' ', '-')
                )
            ))

        self.assert_breadcrumbs(response, extra_breadcrumbs)

    def test_edit_brief_submission(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Organisation the work is for"

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_return_link_to_section_summary_if_section_has_description(
            self, content_loader, data_api_client
    ):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-4/optional2")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Optional 2"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to section 4"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=True, section_name='Section 4')

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_return_link_to_section_summary_if_other_questions(self, content_loader,
    data_api_client):  # noqa
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-1/required1")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Required 1"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to section 1"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=True, section_name='Section 1')

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_return_link_to_brief_overview_if_single_question(self, content_loader,
    data_api_client):  # noqa
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/section-2/required2")

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        secondary_action_link = document.xpath('//form//div[contains(@class, "secondary-action-link")]/a')[0]
        assert document.xpath('//h1')[0].text_content().strip() == "Required 2"
        assert secondary_action_link.get('href').strip() == "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"  # noqa
        assert secondary_action_link.text_content().strip() == "Return to overview"
        self._test_breadcrumbs_on_question_page(response=res, has_summary_page=False)

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_edit_brief_submission_multiquestion(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/section-5/required3")  # noqa

        assert res.status_code == 200

        document = html.fromstring(res.get_data(as_text=True))
        assert document.xpath('//h1')[0].text_content().strip() == "Required 3"
        assert document.xpath(
            '//*[@id="required3_1"]//span[contains(@class, "question-heading")]'
        )[0].text_content().strip() == "Required 3_1"
        assert document.xpath(
            '//*[@id="required3_2"]//span[contains(@class, "question-heading")]'
        )[0].text_content().strip() == "Required 3_2"

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_lot_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-octopuses"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
                "/1234/edit/description-of-work/organisation")

            assert res.status_code == 404

    def test_404_if_brief_has_published_status(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='published')

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/organisation")

        assert res.status_code == 404

    def test_404_if_section_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/not-a-real-section")

        assert res.status_code == 404

    def test_404_if_question_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists"
            "/1234/edit/description-of-work/not-a-real-question")

        assert res.status_code == 404


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestUpdateBriefSubmission(BaseApplicationTest):
    def test_update_brief_submission(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"organisation": "GDS"},
            page_questions=['organisation'],
            updated_by='buyer@email.com'
        )

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_post_update_if_multiple_questions_redirects_to_section_summary(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-1/required1",
            data={
                "required1": True
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"required1": True},
            page_questions=['required1'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1'
        ) is True

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_post_update_if_section_description_redirects_to_section_summary(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-4/optional2",
            data={
                "optional2": True
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"optional2": True},
            page_questions=['optional2'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4'
        ) is True

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_post_update_if_single_question_no_description_redirects_to_overview(self, content_loader, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        content_fixture = ContentLoader('tests/fixtures/content')
        content_fixture.load_manifest('dos', 'data', 'edit_brief')
        content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/section-2/required2",
            data={
                "required2": True
            })

        assert res.status_code == 302
        data_api_client.update_brief.assert_called_with(
            '1234',
            {"required2": True},
            page_questions=['required2'],
            updated_by='buyer@email.com'
        )
        assert res.headers['Location'].endswith(
            'buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234'
        ) is True

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_lot_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_lot_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-octopuses/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='open',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                "digital-specialists/1234/edit/description-of-work/organisation",
                data={
                    "title": "A new title"
                })

            assert res.status_code == 404
            assert not data_api_client.update_brief.called

    def test_404_if_brief_is_already_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/organisation",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_question_does_not_exist(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief()

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/description-of-work/some-made-up-question",
            data={
                "title": "A new title"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestPublishBrief(BaseApplicationTest):
    def test_publish_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'numberOfSuppliers': 5,
            'location': 'somewhere',
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address',
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                               "digital-specialists/1234/publish")
        assert res.status_code == 302
        assert data_api_client.publish_brief.called
        assert res.location == "http://localhost/buyers/frameworks/digital-outcomes-and-specialists/" \
                               "requirements/digital-specialists/1234?published=true"

    def test_publish_brief_with_unanswered_required_questions(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        data_api_client.get_brief.return_value = api_stubs.brief(status="draft")

        res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                               "digital-specialists/1234/publish")
        assert res.status_code == 400
        assert not data_api_client.publish_brief.called

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/edit/your-organisation",
            data={
                "organisation": "GDS"
            })

        assert res.status_code == 404
        assert not data_api_client.update_brief.called

    def test_404_if_framework_status_is_not_live(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill', 'expired']:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )

            brief_json = api_stubs.brief(status="draft")
            brief_questions = brief_json['briefs']
            brief_questions.update({
                'backgroundInformation': 'test background info',
                'contractLength': 'A very long time',
                'culturalFitCriteria': ['CULTURAL', 'FIT'],
                'culturalWeighting': 10,
                'essentialRequirements': 'Everything',
                'evaluationType': ['test evaluation type'],
                'existingTeam': 'team team team',
                'importantDates': 'Near future',
                'numberOfSuppliers': 5,
                'location': 'somewhere',
                'organisation': 'test organisation',
                'priceWeighting': 80,
                'specialistRole': 'communicationsManager',
                'specialistWork': 'work work work',
                'startDate': 'startDate',
                'summary': 'blah',
                'technicalWeighting': 10,
                'workingArrangements': 'arrangements',
                'workplaceAddress': 'address',
                'requirementsLength': '1 week'
            })
            data_api_client.get_brief.return_value = brief_json

            res = self.client.post("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                                   "digital-specialists/1234/publish")
            assert res.status_code == 404
            assert not data_api_client.publish_brief.called

    def test_publish_button_available_if_questions_answered(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'location': 'somewhere',
            'numberOfSuppliers': 3,
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address',
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Publish requirements' in page_html, page_html

    def test_publish_button_unavailable_if_questions_not_answered(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Publish requirements' not in page_html

    def test_warning_about_setting_requirement_length_is_not_displayed_if_not_specialist_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )

        data_api_client.get_brief.return_value = api_stubs.brief(status="draft", lot_slug="digital-outcomes")

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-outcomes/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 2 weeks' in page_html

    def test_correct_content_is_displayed_if_no_requirementLength_is_set(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        data_api_client.get_brief.return_value = api_stubs.brief(status="draft")

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/set-how-long-your-requirements-will-be-open-for/requirementsLength"' in page_html  # noqa
        assert 'This will show you what the supplier application deadline will be' in page_html
        assert 'Your requirements will be open for' not in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_1_week(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '1 week'
        })
        data_api_client.get_brief.return_value = brief_json

        with freeze_time('2016-12-31 23:59:59'):
            res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                                  "digital-specialists/1234/publish")
            page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements will be open for 1 week.' in page_html
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 2 weeks' not in page_html
        assert 'If you publish your requirements today (31 December)' in page_html
        assert 'suppliers will be able to apply until Saturday 7 January 2017 at 11:59pm GMT' in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_2_weeks(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': '2 weeks'
        })
        data_api_client.get_brief.return_value = brief_json

        with freeze_time('2017-07-17 23:59:59'):
            res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                                  "digital-specialists/1234/publish")
            page_html = res.get_data(as_text=True)

        assert res.status_code == 200
        assert 'Your requirements will be open for 2 weeks.' in page_html
        assert 'This will show you what the supplier application deadline will be' not in page_html
        assert 'Your requirements will be open for 1 week' not in page_html
        assert 'If you publish your requirements today (17 July)' in page_html
        assert 'suppliers will be able to apply until Monday 31 July 2017 at 11:59pm GMT' in page_html

    def test_correct_content_is_displayed_if_requirementLength_is_not_set(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'requirementsLength': None
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)
        document = html.fromstring(page_html)

        assert res.status_code == 200
        assert 'Your requirements will be open for 2 weeks.' not in page_html
        assert 'This will show you what the supplier application deadline will be' in page_html
        assert 'Your requirements will be open for 1 week' not in page_html
        assert not document.xpath('//a[contains(text(), "Set how long your requirements will be live for")]')

    def test_heading_for_unanswered_questions_not_displayed_if_only_requirements_length_unset(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )

        brief_json = api_stubs.brief(status="draft")
        brief_questions = brief_json['briefs']
        brief_questions.update({
            'backgroundInformation': 'test background info',
            'contractLength': 'A very long time',
            'culturalFitCriteria': ['CULTURAL', 'FIT'],
            'culturalWeighting': 10,
            'essentialRequirements': 'Everything',
            'evaluationType': ['test evaluation type'],
            'existingTeam': 'team team team',
            'importantDates': 'Near future',
            'location': 'somewhere',
            'numberOfSuppliers': 3,
            'organisation': 'test organisation',
            'priceWeighting': 80,
            'specialistRole': 'communicationsManager',
            'specialistWork': 'work work work',
            'startDate': 'startDate',
            'summary': 'blah',
            'technicalWeighting': 10,
            'workingArrangements': 'arrangements',
            'workplaceAddress': 'address'
        })
        data_api_client.get_brief.return_value = brief_json

        res = self.client.get("/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
                              "digital-specialists/1234/publish")
        page_html = res.get_data(as_text=True)
        document = html.fromstring(page_html)

        assert res.status_code == 200
        assert "You still need to complete the following questions before your requirements " \
            "can be published:" not in page_html


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestDeleteBriefSubmission(BaseApplicationTest):
    def test_delete_brief_submission(self, data_api_client):
        for framework_status in ['live', 'expired']:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete"
            )

            assert res.status_code == 302
            assert data_api_client.delete_brief.called
            assert res.location == "http://localhost/buyers"

    def test_404_if_framework_is_not_live_or_expired(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True)
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete",
            )
            assert res.status_code == 404
            assert not data_api_client.delete_brief.called

    def test_cannot_delete_live_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/delete",
        )

        assert res.status_code == 404
        assert not data_api_client.delete_brief.called

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True)
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/"
            "digital-specialists/1234/delete",
            data={"delete_confirmed": True})

        assert res.status_code == 404


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestBriefSummaryPage(BaseApplicationTest):
    def test_show_draft_brief_summary_page(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="draft")
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200
            page_html = res.get_data(as_text=True)
            document = html.fromstring(page_html)

            assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
            assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                'Title',
                'Specialist role',
                'Location',
                'Description of work',
                'Shortlist and evaluation process',
                'Set how long your requirements will be open for',
                'Describe question and answer session',
                'Review and publish your requirements',
                'How to answer supplier questions',
                'How to shortlist suppliers',
                'How to evaluate suppliers',
                'How to award a contract',
                'View the Digital Outcomes and Specialists contract',
            ]

            assert document.xpath('//a[contains(text(), "Delete")]')

    def test_show_live_brief_summary_page_for_live_and_expired_framework(self, data_api_client):
        framework_statuses = ['live', 'expired']
        with self.app.app_context():
            self.login_as_buyer()
            for framework_status in framework_statuses:
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live")
                brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
                brief_json['briefs']['specialistRole'] = 'communicationsManager'
                brief_json['briefs']["clarificationQuestionsAreClosed"] = True
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                document = html.fromstring(page_html)

                assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
                assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                    'View question and answer dates',
                    'View your published requirements',
                    'Publish questions and answers',
                    'How to answer supplier questions',
                    'How to shortlist suppliers',
                    'How to evaluate suppliers',
                    'How to award a contract',
                    'View the Digital Outcomes and Specialists contract',
                ]

                assert not document.xpath('//a[contains(text(), "Delete")]')

    @pytest.mark.parametrize('status', ['closed', 'cancelled', 'unsuccessful'])
    def test_show_closed_canclled_unsuccessful_brief_summary_page_for_live_and_expired_framework(
            self, data_api_client, status):
        framework_statuses = ['live', 'expired']
        with self.app.app_context():
            self.login_as_buyer()
            for framework_status in framework_statuses:
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status=status)
                brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
                brief_json['briefs']['specialistRole'] = 'communicationsManager'
                brief_json['briefs']["clarificationQuestionsAreClosed"] = True
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                document = html.fromstring(page_html)

                assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
                assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                    'View your published requirements',
                    'View and shortlist suppliers',
                    'How to shortlist suppliers',
                    'How to evaluate suppliers',
                    'How to award a contract',
                    'View the Digital Outcomes and Specialists contract',
                ]

                assert not document.xpath('//a[contains(text(), "Delete")]')

    def test_show_awarded_brief_summary_page_for_live_and_expired_framework(self, data_api_client):
        framework_statuses = ['live', 'expired']
        with self.app.app_context():
            self.login_as_buyer()
            for framework_status in framework_statuses:
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="awarded")
                brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
                brief_json['briefs']['specialistRole'] = 'communicationsManager'
                brief_json['briefs']["clarificationQuestionsAreClosed"] = True
                brief_json['briefs']['awardedBriefResponseId'] = 999
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                document = html.fromstring(page_html)

                assert (document.xpath('//h1')[0]).text_content().strip() == "I need a thing to do a thing"
                assert [e.text_content() for e in document.xpath('//main[@id="content"]//ul/li/a')] == [
                    'View your published requirements',
                    'View and shortlist suppliers',
                    'How to shortlist suppliers',
                    'How to evaluate suppliers',
                    'How to award a contract',
                    'View the Digital Outcomes and Specialists contract',
                ]

                assert not document.xpath('//a[contains(text(), "Delete")]')

    def test_show_clarification_questions_page_for_live_brief_with_no_questions(self, data_api_client):
        framework_statuses = ['live', 'expired']
        with self.app.app_context():
            self.login_as_buyer()
            for framework_status in framework_statuses:
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live")
                brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
                brief_json['briefs']["clarificationQuestionsAreClosed"] = False
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions"  # noqa
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                assert "Supplier questions" in page_html
                assert "No questions or answers have been published" in page_html
                assert "Answer a supplier question" in page_html

    def test_show_clarification_questions_page_for_live_brief_with_one_question(self, data_api_client):
        framework_statuses = ['live', 'expired']
        with self.app.app_context():
            self.login_as_buyer()
            for framework_status in framework_statuses:
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status='live',
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live", clarification_questions=[
                    {"question": "Why is my question a question?",
                     "answer": "Because",
                     "publishedAt": "2016-01-01T00:00:00.000000Z"}
                ])
                brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
                brief_json['briefs']["clarificationQuestionsAreClosed"] = True
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions"  # noqa
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                assert "Supplier questions" in page_html
                assert "Why is my question a question?" in page_html
                assert "Because" in page_html
                assert "Answer a supplier question" in page_html
                assert "No questions or answers have been published" not in page_html

    def test_clarification_questions_page_returns_404_if_not_live_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(status="expired", clarification_questions=[
                {"question": "Why is my question a question?",
                 "answer": "Because",
                 "publishedAt": "2016-01-01T00:00:00.000000Z"}
            ])

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions"  # noqa
            )

            assert res.status_code == 404

    def test_clarification_questions_page_returns_404_if_brief_not_correct(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),  # 'Incorrect' lot slug
                ]
            )
            brief_json = api_stubs.brief(status="live", clarification_questions=[
                {"question": "Why is my question a question?",
                 "answer": "Because",
                 "publishedAt": "2016-01-01T00:00:00.000000Z"}
            ])
            brief_json['briefs']['lotSlug'] = "wrong lot slug"
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions"  # noqa
            )

            assert res.status_code == 404

    def test_404_if_framework_does_not_allow_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=False),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 404

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(user_id=234)

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 404

    @mock.patch("app.main.views.buyers.content_loader", autospec=True)
    def test_links_to_sections_go_to_the_correct_pages_whether_they_be_sections_or_questions(self, content_loader, data_api_client):  # noqa
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief()

            content_fixture = ContentLoader('tests/fixtures/content')
            content_fixture.load_manifest('dos', 'data', 'edit_brief')
            content_loader.get_manifest.return_value = content_fixture.get_manifest('dos', 'edit_brief')

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234"
            )

            assert res.status_code == 200

            document = html.fromstring(res.get_data(as_text=True))
            section_steps = document.xpath(
                '//*[@id="content"]/div/div/ol[contains(@class, "instruction-list")]')
            section_1_link = section_steps[0].xpath('li//a[contains(text(), "Section 1")]')
            section_2_link = section_steps[0].xpath('li//a[contains(text(), "Section 2")]')
            section_4_link = section_steps[0].xpath('li//a[contains(text(), "Section 4")]')

            # section with multiple questions
            assert section_1_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-1'
            # section with single question
            assert section_2_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/edit/section-2/required2'  # noqa
            # section with single question and a description
            assert section_4_link[0].get('href').strip() == \
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/section-4'

    def test_no_meta_data_is_shown_for_a_draft_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug="digital-outcomes-and-specialists-2",
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(
                status="draft",
                framework_slug="digital-outcomes-and-specialists-2",
                framework_name="Digital Outcomes and Specialists 2",
            )

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-specialists/1234"
            )
            assert res.status_code == 200

            document = html.fromstring(res.get_data(as_text=True))

            meta_data_container = document.xpath('//*[@id="requirements-meta"]')

            assert not meta_data_container

    def test_shows_correct_content_for_draft_open_and_closed_dos_1_and_2_briefs(self, data_api_client):
        framework_slugs = ["digital-outcomes-and-specialists", "digital-outcomes-and-specialists-2"]
        framework_names = ["Digital Outcomes and Specialists", "Digital Outcomes and Specialists 2"]
        sidebar_heading_content = ['Closing', 'Closed']
        brief_statuses = ['live', 'closed']

        for framework_slug, framework_name in zip(framework_slugs, framework_names):
            with self.app.app_context():
                self.login_as_buyer()
                for heading, brief_status in zip(sidebar_heading_content, brief_statuses):
                    data_api_client.get_framework.return_value = api_stubs.framework(
                        slug=framework_slug,
                        status='live',
                        lots=[
                            api_stubs.lot(slug='digital-specialists', allows_brief=True),
                        ]
                    )
                    data_api_client.get_brief.return_value = api_stubs.brief(
                        status=brief_status,
                        framework_slug=framework_slug,
                        framework_name=framework_name,
                    )

                    res = self.client.get(
                        "/buyers/frameworks/{}/requirements/digital-specialists/1234".format(framework_slug)
                    )
                    assert res.status_code == 200

                    document = html.fromstring(res.get_data(as_text=True))

                    sidebar_headings = document.xpath('//*[@class="sidebar-heading"]/text()')
                    sidebar_content = document.xpath('//*[@class="sidebar-content"]/text()')
                    framework_name_content = document.xpath('//*[@class="framework-name"]/a/text()')[0]

                    assert sidebar_headings == ['Published', heading, 'Framework']
                    assert sidebar_content == ['Tuesday 29 March 2016', 'Thursday 7 April 2016']
                    assert framework_name_content == framework_name

    def test_links_to_correct_call_off_contract_and_framework_agreement_for_briefs_framework(self, data_api_client):
        framework_slugs = ["digital-outcomes-and-specialists", "digital-outcomes-and-specialists-2"]
        framework_names = ["Digital Outcomes and Specialists", "Digital Outcomes and Specialists 2"]
        call_off_contract_urls = [
            "https://www.gov.uk/government/publications/digital-outcomes-and-specialists-call-off-contract",
            "https://www.gov.uk/government/publications/digital-outcomes-and-specialists-2-call-off-contract"
        ]
        framework_agreement_urls = [
            "https://www.gov.uk/government/publications/digital-outcomes-and-specialists-framework-agreement",
            "https://www.gov.uk/government/publications/digital-outcomes-and-specialists-2-framework-agreement"
        ]

        for framework_slug, framework_name, call_off_contract_url, framework_agreement_url in \
                zip(framework_slugs, framework_names, call_off_contract_urls, framework_agreement_urls):
                with self.app.app_context():
                    self.login_as_buyer()
                    data_api_client.get_framework.return_value = api_stubs.framework(
                        slug=framework_slug,
                        status='live',
                        lots=[
                            api_stubs.lot(slug='digital-specialists', allows_brief=True),
                        ]
                    )
                    data_api_client.get_brief.return_value = api_stubs.brief(
                        status='live',
                        framework_slug=framework_slug,
                        framework_name=framework_name,
                    )

                    res = self.client.get(
                        "/buyers/frameworks/{}/requirements/digital-specialists/1234".format(framework_slug)
                    )
                    assert res.status_code == 200

                    document = html.fromstring(res.get_data(as_text=True))

                    call_off_contract_link_destination = \
                        document.xpath('//main[@id="content"]//ul/li/a')[-1].values()[0]
                    framework_agreement_link_destination = \
                        document.xpath('//*[@class="framework-name"]/a')[0].values()[0]
                    contract_link_text = document.xpath('//main[@id="content"]//ul/li/a/text()')[-1]

                    assert call_off_contract_link_destination == call_off_contract_url
                    assert framework_agreement_link_destination == framework_agreement_url
                    assert contract_link_text == "View the {} contract".format(framework_name)


@mock.patch("app.main.views.buyers.data_api_client", autospec=True)
class TestAddBriefClarificationQuestion(BaseApplicationTest):
    def test_show_brief_clarification_question_form_for_live_and_expired_framework(self, data_api_client):
        framework_statuses = ['live', 'expired']
        self.login_as_buyer()
        for framework_status in framework_statuses:
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug="digital-outcomes-and-specialists",
                status=framework_status,
                lots=[
                    api_stubs.lot(slug="digital-specialists", allows_brief=True)
                ])
            brief_json = api_stubs.brief(status="live")
            brief_json['briefs']["clarificationQuestionsAreClosed"] = False
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
                "/digital-specialists/1234/supplier-questions/answer-question")

            assert res.status_code == 200

    def test_add_brief_clarification_question_for_live_and_expired_framework(self, data_api_client):
        framework_statuses = ['live', 'expired']
        self.login_as_buyer()
        for framework_status in framework_statuses:
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug="digital-outcomes-and-specialists",
                status=framework_status,
                lots=[
                    api_stubs.lot(slug="digital-specialists", allows_brief=True)
                ])
            brief_json = api_stubs.brief(status="live")
            brief_json['briefs']["clarificationQuestionsAreClosed"] = False
            data_api_client.get_brief.return_value = brief_json

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
                "/digital-specialists/1234/supplier-questions/answer-question",
                data={
                    "question": "Why?",
                    "answer": "Because",
                })

            assert res.status_code == 302
            data_api_client.add_brief_clarification_question.assert_called_with(
                "1234", "Why?", "Because", "buyer@email.com")

            # test that the redirect ends up on the right page
            assert res.headers['Location'].endswith(
                '/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/supplier-questions'  # noqa
            ) is True

    def test_404_if_framework_is_not_live_or_expired(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief()
            brief_json['briefs']["clarificationQuestionsAreClosed"] = False
            data_api_client.get_brief.return_value = brief_json

            res = self.client.post(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
                "/digital-specialists/1234/supplier-questions/answer-question",
                data={
                    "question": "Why?",
                    "answer": "Because",
                })

            assert res.status_code == 404
            assert not data_api_client.add_brief_clarification_question.called

    def test_404_if_framework_does_not_allow_brief(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=False),
            ]
        )
        brief_json = api_stubs.brief()
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_404_if_brief_does_not_belong_to_user(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        brief_json = api_stubs.brief(user_id=234)
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_404_if_brief_is_not_live(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        brief_json = api_stubs.brief(status="draft")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 404
        assert not data_api_client.add_brief_clarification_question.called

    def test_validation_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug="digital-outcomes-and-specialists",
            status="live",
            lots=[
                api_stubs.lot(slug="digital-specialists", allows_brief=True)
            ])
        brief_json = api_stubs.brief(status="live")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json
        data_api_client.add_brief_clarification_question.side_effect = HTTPError(
            mock.Mock(status_code=400),
            {"question": "answer_required"})

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        assert len(document.cssselect(".validation-message")) == 1, res.get_data(as_text=True)

    def test_api_error(self, data_api_client):
        self.login_as_buyer()
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug="digital-outcomes-and-specialists",
            status="live",
            lots=[
                api_stubs.lot(slug="digital-specialists", allows_brief=True)
            ])
        brief_json = api_stubs.brief(status="live")
        brief_json['briefs']["clarificationQuestionsAreClosed"] = False
        data_api_client.get_brief.return_value = brief_json
        data_api_client.add_brief_clarification_question.side_effect = HTTPError(
            mock.Mock(status_code=500))

        res = self.client.post(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements"
            "/digital-specialists/1234/supplier-questions/answer-question",
            data={
                "question": "Why?",
                "answer": "Because",
            })

        assert res.status_code == 500


class AbstractViewBriefResponsesPage(BaseApplicationTest):
    def setup_method(self, method):
        super(AbstractViewBriefResponsesPage, self).setup_method(method)

        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )

        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='closed')
        brief_stub['briefs'].update({'publishedAt': self.brief_publishing_date})
        self.data_api_client.get_brief.return_value = brief_stub

        self.data_api_client.find_brief_responses.return_value = self.brief_responses

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super(AbstractViewBriefResponsesPage, self).teardown_method(method)

    def test_page_shows_correct_content_when_eligible_responses(self):
        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "Shortlist suppliers" in page
        assert "2 suppliers" in page
        assert "responded to your requirements and meet all your essential skills and experience." in page
        assert (
            "Any suppliers that did not meet all your essential requirements "
            "have already been told they were unsuccessful."
        ) in page

    @pytest.mark.parametrize('status', buyers.CLOSED_PUBLISHED_BRIEF_STATUSES)
    def test_page_visible_for_awarded_cancelled_unsuccessful_briefs(self, status):
        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='closed')
        brief_stub['briefs'].update(
            {
                'publishedAt': self.brief_publishing_date,
                'status': status
            }
        )
        if status == 'awarded':
            brief_stub['briefs']['awardedBriefResponseId'] = 999

        self.data_api_client.get_brief.return_value = brief_stub
        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        assert res.status_code == 200

    def test_page_does_not_pluralise_for_single_response(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": [self.brief_responses["briefResponses"][0]]
        }

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)
        assert res.status_code == 200
        assert "1 supplier" in page
        assert "responded to your requirements and meets all your essential skills and experience." in page

    def test_404_if_brief_does_not_belong_to_buyer(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", user_id=234)

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404

    def test_404_if_brief_is_not_closed_or_awarded(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", status='live')

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404

    def test_404_if_lot_does_not_allow_brief(self):
        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=False),
            ]
        )

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )

        assert res.status_code == 404


class TestViewBriefResponsesPageForLegacyBrief(AbstractViewBriefResponsesPage):
    brief_responses = {
        "briefResponses": [
            {"essentialRequirements": [True, True, True, True, True]},
            {"essentialRequirements": [True, False, True, True, True]},
            {"essentialRequirements": [True, True, False, False, True]},
            {"essentialRequirements": [True, True, True, True, True]},
            {"essentialRequirements": [True, True, True, True, False]},
        ]
    }

    brief_publishing_date = '2016-01-21T12:00:00.000000Z'

    def test_page_shows_correct_message_for_legacy_brief_if_no_eligible_responses(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": [self.brief_responses["briefResponses"][1]]
        }

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "There were no applications" in page
        assert "No suppliers met your essential skills and experience requirements." in page
        assert "All the suppliers who applied have already been told they were unsuccessful." in page

    def test_page_shows_csv_download_link(self):
        self.data_api_client.get_brief.return_value = api_stubs.brief(lot_slug="digital-outcomes", status='closed')

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        document = html.fromstring(res.get_data(as_text=True))
        csv_link = document.xpath(
            '//a[@href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses/download"]'  # noqa
        )[0]

        assert res.status_code == 200
        assert self._strip_whitespace(csv_link.text_content()) == \
            "CSVdocument:Downloadsupplierresponsesto‘Ineedathingtodoathing’"


class TestViewBriefResponsesPageForNewFlowBrief(AbstractViewBriefResponsesPage):
    brief_responses = {
        "briefResponses": [
            {"essentialRequirementsMet": True, "essentialRequirements": [{"evidence": "blah"}]},
            {"essentialRequirementsMet": True, "essentialRequirements": [{"evidence": "blah"}]},
        ]
    }

    brief_publishing_date = '2017-01-21T12:00:00.000000Z'

    def test_page_shows_correct_message_for_no_responses(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": []
        }

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        page = res.get_data(as_text=True)

        assert res.status_code == 200
        assert "There were no applications" in page
        assert "No suppliers met your essential skills and experience requirements." in page
        assert "All the suppliers who applied have already been told they were unsuccessful." not in page

    def test_page_shows_ods_download_link(self):
        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='closed')
        brief_stub['briefs'].update({'publishedAt': self.brief_publishing_date})
        self.data_api_client.get_brief.return_value = brief_stub

        self.login_as_buyer()
        res = self.client.get(
            "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses"
        )
        document = html.fromstring(res.get_data(as_text=True))
        csv_link = document.xpath(
            '//a[@href="/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-outcomes/1234/responses/download"]'  # noqa
        )[0]

        assert res.status_code == 200
        assert self._strip_whitespace(csv_link.text_content()) == \
            "ODSdocument:Downloadsupplierresponsestothisrequirement"


class TestDownloadBriefResponsesView(BaseApplicationTest):
    def setup_method(self, method):
        super(TestDownloadBriefResponsesView, self).setup_method(method)

        self.data_api_client = mock.MagicMock(spec_set=DataAPIClient)
        self.content_loader = mock.MagicMock(spec_set=ContentLoader)

        self.instance = buyers.DownloadBriefResponsesView(
            data_api_client=self.data_api_client,
            content_loader=self.content_loader
        )

        self.brief = api_stubs.brief(status='closed')['briefs']
        self.brief['essentialRequirements'] = [
            "Good nose for tea",
            "Good eye for biscuits",
            "Knowledgable about tea"
        ]
        self.brief['niceToHaveRequirements'] = [
            "Able to bake",
            "Able to perform the tea ceremony"
        ]
        self.brief['blah'] = ['Affirmative', 'Negative']

        self.responses = [
            {
                "supplierName": "Prof. T. Maker",
                "respondToEmailAddress": "t.maker@example.com",
                "niceToHaveRequirements": [
                    {
                        "yesNo": False
                    },
                    {
                        "yesNo": False
                    }
                ],
                "availability": "2017-12-25",
                "essentialRequirementsMet": True,
                "essentialRequirements": [
                    {
                        "evidence": "From Assan to Yixing I've got you covered."
                    },
                    {
                        "evidence": "There will be no nobhobs or cream custards on my watch."
                    },
                    {
                        "evidence": "I even memorised the entire T section of the dictionary"
                    }
                ],
                "dayRate": "750",
                "blah": [True, False]
            },
            {
                "supplierName": "Tea Boy Ltd.",
                "respondToEmailAddress": "teaboy@example.com",
                "niceToHaveRequirements": [
                    {
                        "yesNo": True,
                        "evidence": "Winner of GBBO 2009"
                    },
                    {
                        "yesNo": True,
                        "evidence": "Currently learning from the re-incarnation of Eisai himself"
                    }
                ],
                "availability": "Tomorrow",
                "essentialRequirementsMet": True,
                "essentialRequirements": [
                    {
                        "evidence": "I know my Silver needle from my Red lychee"
                    },
                    {
                        "evidence": "Able to identify fake hobnobs and custard cremes a mile off"
                    },
                    {
                        "evidence": "Have visited the Flagstaff House Museum of Tea Ware in Hong Kong"
                    }
                ],
                "dayRate": "1000",
                "blah": [False, True]
            }
        ]

    def teardown_method(self, method):
        self.instance = None

        super(TestDownloadBriefResponsesView, self).teardown_method(method)

    @pytest.mark.parametrize('brief_status', buyers.CLOSED_PUBLISHED_BRIEF_STATUSES)
    def test_end_to_end_for_closed_awarded_cancelled_unsuccessful_briefs(self, brief_status):
        self.brief['status'] = brief_status
        if brief_status == 'awarded':
            self.brief['awardedBriefResponseId'] = 999
        for framework_status in ['live', 'expired']:
            self.data_api_client.find_brief_responses.return_value = {
                'briefResponses': self.responses
            }
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            self.data_api_client.get_brief.return_value = {'briefs': self.brief}

            with mock.patch.object(buyers, 'data_api_client', self.data_api_client):
                self.login_as_buyer()
                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists"
                    "/requirements/digital-specialists/1234/responses/download"
                )

            assert res.status_code == 200
            assert res.mimetype == 'application/vnd.oasis.opendocument.spreadsheet'
            assert len(res.data) > 100

    def test_404_if_framework_is_not_live_or_expired(self):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            self.data_api_client.find_brief_responses.return_value = {
                'briefResponses': self.responses
            }
            self.data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            self.data_api_client.get_brief.return_value = {'briefs': self.brief}

            with mock.patch.object(buyers, 'data_api_client', self.data_api_client):
                self.login_as_buyer()
                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists"
                    "/requirements/digital-specialists/1234/responses/download"
                )

            assert res.status_code == 404

    def test_get_responses(self):
        brief = mock.Mock()

        with po(buyers, 'get_sorted_responses_for_brief') as m:
            result = self.instance.get_responses(brief)

        assert result == m.return_value

        m.assert_called_once_with(brief, self.instance.data_api_client)

    def test_get_question(self):
        framework_slug = mock.Mock()
        lot_slug = mock.Mock()
        manifest = mock.Mock()

        obj = self.content_loader.get_manifest.return_value
        content = obj.filter.return_value

        result = self.instance.get_questions(framework_slug, lot_slug, manifest)

        assert result == content.get_section.return_value.questions

        self.content_loader.get_manifest\
            .assert_called_once_with(framework_slug, manifest)

        obj.filter.assert_called_once_with({'lot': lot_slug}, dynamic=False)

        content.get_section\
               .assert_called_once_with('view-response-to-requirements')

    def test_get_question_fails_with_empty_list(self):
        framework_slug = mock.Mock()
        lot_slug = mock.Mock()
        manifest = mock.Mock()

        self.content_loader.get_manifest.return_value\
                           .filter.return_value\
                           .get_section.return_value = None

        result = self.instance.get_questions(framework_slug, lot_slug, manifest)

        assert result == []

    def test_get_context_data(self):
        self.instance.get_responses = mock.Mock()

        brief = api_stubs.brief(status='closed')

        kwargs = {
            'brief_id': mock.Mock(),
            'framework_slug': mock.Mock(),
            'lot_slug': mock.Mock()
        }

        text_type = str if sys.version_info[0] == 3 else unicode

        filename = inflection.parameterize(text_type(brief['briefs']['title']))

        expected = dict(**kwargs)
        expected['brief'] = brief['briefs']
        expected['responses'] = self.instance.get_responses.return_value
        expected['filename'] = 'supplier-responses-' + filename

        self.instance.data_api_client.get_brief.return_value = brief

        with po(buyers, 'get_framework_and_lot') as get_framework_and_lot,\
                po(buyers, 'is_brief_correct') as is_brief_correct,\
                mock.patch.object(buyers, 'current_user') as current_user:

            result = self.instance.get_context_data(**kwargs)

        is_brief_correct.assert_called_once_with(brief['briefs'],
                                                 kwargs['framework_slug'],
                                                 kwargs['lot_slug'],
                                                 current_user.id)

        self.instance.data_api_client.get_brief\
            .assert_called_once_with(kwargs['brief_id'])

        self.instance.get_responses\
            .assert_called_once_with(brief['briefs'])

        assert result == expected

    def test_get_context_data_with_incorrect_brief(self):
        self.instance.get_responses = mock.Mock()

        brief = api_stubs.brief(status='closed')

        kwargs = {
            'brief_id': mock.Mock(),
            'framework_slug': mock.Mock(),
            'lot_slug': mock.Mock()
        }

        self.instance.data_api_client.get_brief.return_value = brief

        with po(buyers, 'get_framework_and_lot') as get_framework_and_lot,\
                po(buyers, 'is_brief_correct') as is_brief_correct,\
                mock.patch.object(buyers, 'current_user') as current_user:

            is_brief_correct.return_value = False
            with pytest.raises(NotFound):
                self.instance.get_context_data(**kwargs)

    def test_get_context_data_with_open_brief(self):
        self.instance.get_responses = mock.Mock()

        brief = api_stubs.brief(status='live')

        kwargs = {
            'brief_id': mock.Mock(),
            'framework_slug': mock.Mock(),
            'lot_slug': mock.Mock()
        }

        self.instance.data_api_client.get_brief.return_value = brief

        with po(buyers, 'get_framework_and_lot') as get_framework_and_lot,\
                po(buyers, 'is_brief_correct') as is_brief_correct,\
                mock.patch.object(buyers, 'current_user') as current_user:

            is_brief_correct.return_value = True
            with pytest.raises(NotFound):
                self.instance.get_context_data(**kwargs)

    def test_generate_ods(self):
        questions = [
            {'id': 'supplierName', 'name': 'Supplier', 'type': 'text'},
            {'id': 'respondToEmailAddress', 'name': 'Email address', 'type': 'text'},
            {'id': 'availability', 'name': 'Availability', 'type': 'text'},
            {'id': 'dayRate', 'name': 'Day rate', 'type': 'text'},
        ]

        self.instance.get_questions = mock.Mock(return_value=[
            Question(question) for question in questions
        ])

        doc = self.instance.generate_ods(self.brief, self.responses)

        sheet = doc.sheet("Supplier evidence")

        assert sheet.read_cell(0, 0) == self.brief['title']

        for i, question in enumerate(questions):
            assert sheet.read_cell(0, i + 1) == question['name']
            assert sheet.read_cell(1, i + 1) == ''

            for j, response in enumerate(self.responses):
                assert sheet.read_cell(j + 2, i + 1) == response[question['id']]

    def test_generate_ods_with_boolean_list(self):
        questions = [
            {'id': 'blah', 'name': 'Blah Blah', 'type': 'boolean_list'},
        ]

        self.instance.get_questions = mock.Mock(return_value=[
            Question(question) for question in questions
        ])

        doc = self.instance.generate_ods(self.brief, self.responses)

        sheet = doc.sheet("Supplier evidence")

        k = 0

        for i, question in enumerate(questions):
            length = len(self.brief[question['id']])
            offset = 0

            for l, name in enumerate(self.brief[question['id']]):
                k += 1

                if l == 0:
                    assert sheet.read_cell(0, k) == question['name']
                else:
                    assert sheet.read_cell(0, k) == ''

                assert sheet.read_cell(1, k) == name

                for j, response in enumerate(self.responses):
                    assert sheet.read_cell(j + 2, k) == str(response[question['id']][l]).lower()

    def test_generate_ods_with_dynamic_list(self):
        questions = [
            {'id': 'niceToHaveRequirements', 'name': 'Nice-to-have skills & evidence', 'type': 'dynamic_list'},
            {'id': 'essentialRequirements', 'name': 'Essential skills & evidence', 'type': 'dynamic_list'},
        ]

        self.instance.get_questions = mock.Mock(return_value=[
            Question(question) for question in questions
        ])

        doc = self.instance.generate_ods(self.brief, self.responses)

        sheet = doc.sheet("Supplier evidence")

        k = 0

        for i, question in enumerate(questions):
            length = len(self.brief[question['id']])
            offset = 0

            for l, name in enumerate(self.brief[question['id']]):
                k += 1

                if l == 0:
                    assert sheet.read_cell(0, k) == question['name']
                else:
                    assert sheet.read_cell(0, k) == ''

                assert sheet.read_cell(1, k) == name

                for j, response in enumerate(self.responses):
                    assert sheet.read_cell(j + 2, k) == response[question['id']][l].get('evidence', '')

    def test_generate_ods_missing_with_dynamic_list(self):
        questions = [
            {'id': 'niceToHaveRequirements', 'name': 'Nice-to-have skills & evidence', 'type': 'dynamic_list'},
            {'id': 'essentialRequirements', 'name': 'Essential skills & evidence', 'type': 'dynamic_list'},
        ]

        self.instance.get_questions = mock.Mock(return_value=[
            Question(question) for question in questions
        ])

        self.brief['niceToHaveRequirements'] = []

        del self.responses[0]['niceToHaveRequirements']
        del self.responses[1]['niceToHaveRequirements']

        doc = self.instance.generate_ods(self.brief, self.responses)

        sheet = doc.sheet("Supplier evidence")

        k = 0

        for l, name in enumerate(self.brief['essentialRequirements']):
            k += 1

            for j, response in enumerate(self.responses):
                assert sheet.read_cell(j + 2, k) == response['essentialRequirements'][l].get('evidence', '')

    def test_create_ods_response(self):
        context = {'brief': api_stubs.brief(status='closed')['briefs'],
                   'responses': mock.Mock(),
                   'filename': 'foobar'}

        self.instance.generate_ods = mock.Mock()

        with po(buyers, 'BytesIO') as BytesIO,\
                po(buyers, 'Response') as Response:

            result = self.instance.create_ods_response(context)

        assert result == (Response.return_value, 200)

        BytesIO.assert_called_once_with()

        buf = BytesIO.return_value

        self.instance.generate_ods.assert_called_once_with(context['brief'],
                                                           context['responses'])

        self.instance.generate_ods.return_value.save.assert_called_once_with(buf)

        Response.assert_called_once_with(
            buf.getvalue.return_value,
            mimetype='application/vnd.oasis.opendocument.spreadsheet',
            headers={
                "Content-Disposition": (
                    "attachment;filename=foobar.ods"
                ).format(context['brief']['id']),
                "Content-Type": "application/vnd.oasis.opendocument.spreadsheet"
            }
        )

    def test_create_response(self):
        self.instance.create_ods_response = mock.Mock()
        self.instance.create_csv_response = mock.Mock()

        context = {'responses': [{'essentialRequirementsMet': True}]}

        result = self.instance.create_response(context)

        assert result == self.instance.create_ods_response.return_value

        self.instance.create_ods_response.assert_called_once_with(context)

        self.instance.create_ods_response = mock.Mock()
        self.instance.create_csv_response = mock.Mock()

        context = {'responses': [{}]}

        result = self.instance.create_response(context)

        assert result == self.instance.create_csv_response.return_value

        self.instance.create_csv_response.assert_called_once_with(context)

    def test_dispatch_request(self):
        kwargs = {'foo': 'bar', 'baz': 'abc'}

        self.instance.get_context_data = get_context_data = mock.Mock()

        self.instance.create_response = create_response = mock.Mock()

        result = self.instance.dispatch_request(**kwargs)

        assert create_response.return_value == result

        self.instance.get_context_data.assert_called_once_with(**kwargs)


@mock.patch("app.main.views.buyers.data_api_client", autospec=True)
class TestDownloadBriefResponsesCsv(BaseApplicationTest):
    url = "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/responses/download"

    def setup_method(self, method):
        super(TestDownloadBriefResponsesCsv, self).setup_method(method)
        self.brief = api_stubs.brief(status='closed')
        self.brief['briefs']['essentialRequirements'] = ["E1", "E2"]
        self.brief['briefs']['niceToHaveRequirements'] = ["Nice1", "Nice2", "Nice3"]

        self.brief_responses = {
            "briefResponses": [
                {
                    "supplierName": "Kev's Butties",
                    "availability": "Next Tuesday",
                    "dayRate": "£1.49",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [True, False, False],
                    "respondToEmailAddress": "test1@email.com",
                },
                {
                    "supplierName": "Kev's Pies",
                    "availability": "A week Friday",
                    "dayRate": "£3.50",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [False, True, True],
                    "respondToEmailAddress": "test2@email.com",
                },
                {
                    "supplierName": "Kev's Doughnuts",
                    "availability": "As soon as the sugar is delivered",
                    "dayRate": "£10 a dozen",
                    "essentialRequirements": [True, False],
                    "niceToHaveRequirements": [True, True, False],
                    "respondToEmailAddress": "test3@email.com",
                },
                {
                    "supplierName": "Kev's Fried Noodles",
                    "availability": "After Christmas",
                    "dayRate": "£12.35",
                    "essentialRequirements": [False, True],
                    "niceToHaveRequirements": [True, True, True],
                    "respondToEmailAddress": "test4@email.com",
                },
                {
                    "supplierName": "Kev's Pizza",
                    "availability": "Within the hour",
                    "dayRate": "£350",
                    "essentialRequirements": [False, False],
                    "niceToHaveRequirements": [False, False, False],
                    "respondToEmailAddress": "test5@email.com",
                },
            ]
        }

        self.tricky_character_responses = {
            "briefResponses": [
                {
                    "supplierName": "K,ev’s \"Bu,tties",
                    "availability": "❝Next — Tuesday❞",
                    "dayRate": "¥1.49,",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [True, False, False],
                    "respondToEmailAddress": "test1@email.com",
                },
                {
                    "supplierName": "Kev\'s \'Pies",
                    "availability": "&quot;A week Friday&rdquot;",
                    "dayRate": "&euro;3.50",
                    "essentialRequirements": [True, True],
                    "niceToHaveRequirements": [False, True, True],
                    "respondToEmailAddress": "te,st2@email.com",
                },
            ]
        }

    @pytest.mark.parametrize('brief_status', buyers.CLOSED_PUBLISHED_BRIEF_STATUSES)
    def test_csv_includes_all_eligible_responses_and_no_ineligible_responses(self, data_api_client, brief_status):
        self.brief['status'] = brief_status
        if brief_status == 'awarded':
            self.brief['awardedBriefResponseId'] = 999
        for framework_status in ['live', 'expired']:
            data_api_client.find_brief_responses.return_value = self.brief_responses
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = self.brief

            self.login_as_buyer()
            res = self.client.get(self.url)
            page = res.get_data(as_text=True)
            lines = page.splitlines()
            # There are only the two eligible responses included
            assert len(lines) == 3
            assert lines[0] == "Supplier,Date the specialist can start work,Day rate,Nice1,Nice2,Nice3,Email address"
            # The response with two nice-to-haves is sorted to above the one with only one
            assert lines[1] == "Kev's Pies,A week Friday,£3.50,False,True,True,test2@email.com"
            assert lines[2] == "Kev's Butties,Next Tuesday,£1.49,True,False,False,test1@email.com"

    def test_download_brief_responses_for_brief_without_nice_to_haves(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )

        for response in self.brief_responses['briefResponses']:
            del response["niceToHaveRequirements"]
        data_api_client.find_brief_responses.return_value = self.brief_responses

        data_api_client.get_brief.return_value = self.brief

        self.login_as_buyer()

        del self.brief['briefs']['niceToHaveRequirements']
        res = self.client.get(self.url)
        assert res.status_code, 200

        self.brief['briefs']['niceToHaveRequirements'] = []
        res = self.client.get(self.url)
        assert res.status_code, 200

    def test_csv_handles_tricky_characters(self, data_api_client):
        data_api_client.find_brief_responses.return_value = self.tricky_character_responses
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = self.brief

        self.login_as_buyer()
        res = self.client.get(self.url)
        page = res.get_data(as_text=True)
        lines = page.splitlines()

        assert len(lines) == 3
        assert lines[0] == "Supplier,Date the specialist can start work,Day rate,Nice1,Nice2,Nice3,Email address"
        # The values with internal commas are surrounded by quotes, and all other characters appear as in the data
        assert lines[1] == 'Kev\'s \'Pies,&quot;A week Friday&rdquot;,&euro;3.50,False,True,True,"te,st2@email.com"'
        assert lines[2] == '"K,ev’s ""Bu,tties",❝Next — Tuesday❞,"¥1.49,",True,False,False,test1@email.com'

    def test_404_if_brief_does_not_belong_to_buyer(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(user_id=234, status='closed')

        self.login_as_buyer()
        res = self.client.get(self.url)
        assert res.status_code == 404

    def test_404_if_brief_is_not_closed_or_awarded(self, data_api_client):
        data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-specialists', allows_brief=True),
            ]
        )
        data_api_client.get_brief.return_value = api_stubs.brief(status='live')

        self.login_as_buyer()
        res = self.client.get(self.url)
        assert res.status_code == 404

    def test_404_if_framework_is_not_live_or_expired(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status=framework_status,
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            data_api_client.get_brief.return_value = api_stubs.brief(status='closed')

            self.login_as_buyer()
            res = self.client.get(self.url)
            assert res.status_code == 404


@mock.patch('app.main.views.buyers.data_api_client', autospec=True)
class TestViewQuestionAndAnswerDates(BaseApplicationTest):
    def test_show_question_and_answer_dates_for_published_brief(self, data_api_client):
        for framework_status in ['live', 'expired']:
            with self.app.app_context():
                self.login_as_buyer()
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live")
                brief_json['briefs']['requirementsLength'] = '2 weeks'
                brief_json['briefs']['publishedAt'] = u"2016-04-02T20:10:00.00000Z"
                brief_json['briefs']['clarificationQuestionsClosedAt'] = u"2016-04-12T23:59:00.00000Z"
                brief_json['briefs']['clarificationQuestionsPublishedBy'] = u"2016-04-14T23:59:00.00000Z"
                brief_json['briefs']['applicationsClosedAt'] = u"2016-04-16T23:59:00.00000Z"
                brief_json['briefs']['specialistRole'] = 'communicationsManager'
                brief_json['briefs']["clarificationQuestionsAreClosed"] = True
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
                )

                assert res.status_code == 200
                page_html = res.get_data(as_text=True)
                document = html.fromstring(page_html)

                assert (document.xpath('//h1')[0]).text_content().strip() == "Question and answer dates"
                assert all(
                    date in
                    [e.text_content() for e in document.xpath('//main[@id="content"]//th/span')]
                    for date in ['2 April', '8 April', '15 April', '16 April']
                )

    def test_404_if_framework_is_not_live_or_expired(self, data_api_client):
        for framework_status in ['coming', 'open', 'pending', 'standstill']:
            with self.app.app_context():
                self.login_as_buyer()
                data_api_client.get_framework.return_value = api_stubs.framework(
                    slug='digital-outcomes-and-specialists',
                    status=framework_status,
                    lots=[
                        api_stubs.lot(slug='digital-specialists', allows_brief=True),
                    ]
                )
                brief_json = api_stubs.brief(status="live")
                data_api_client.get_brief.return_value = brief_json

                res = self.client.get(
                    "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
                )

                assert res.status_code == 404

    def test_do_not_show_question_and_answer_dates_for_draft_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="draft")
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 404

    def test_do_not_show_question_and_answer_dates_for_closed_brief(self, data_api_client):
        with self.app.app_context():
            self.login_as_buyer()
            data_api_client.get_framework.return_value = api_stubs.framework(
                slug='digital-outcomes-and-specialists',
                status='live',
                lots=[
                    api_stubs.lot(slug='digital-specialists', allows_brief=True),
                ]
            )
            brief_json = api_stubs.brief(status="closed")
            brief_json['briefs']['publishedAt'] = "2016-04-02T20:10:00.00000Z"
            brief_json['briefs']['specialistRole'] = 'communicationsManager'
            brief_json['briefs']["clarificationQuestionsAreClosed"] = True
            data_api_client.get_brief.return_value = brief_json

            res = self.client.get(
                "/buyers/frameworks/digital-outcomes-and-specialists/requirements/digital-specialists/1234/timeline"
            )

            assert res.status_code == 404


class TestAwardBrief(BaseApplicationTest):
    brief_responses = {
        "briefResponses": [
            {"id": 23, "supplierName": "Dobbins"},
            {"id": 4444, "supplierName": "Cobbins"},
            {"id": 2, "supplierName": "Aobbins"},
            {"id": 90, "supplierName": "Bobbins"},
        ]
    }
    url = "/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/{brief_id}/award-contract"  # noqa

    def setup_method(self, method):
        super(TestAwardBrief, self).setup_method(method)

        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists-2',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )

        brief_stub = api_stubs.brief(
            framework_slug="digital-outcomes-and-specialists-2", lot_slug="digital-outcomes", status='closed'
        )
        self.data_api_client.get_brief.return_value = brief_stub

        self.data_api_client.find_brief_responses.return_value = self.brief_responses

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super(TestAwardBrief, self).teardown_method(method)

    def test_award_brief_200s_with_correct_default_content(self):
        self.login_as_buyer()

        res = self.client.get(self.url.format(brief_id=1234))

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        self.assert_breadcrumbs(res, extra_breadcrumbs=[
            (
                'I need a thing to do a thing',
                '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/1234'
            )
        ])

        page_title = self._strip_whitespace(document.xpath('//h1')[0].text_content())
        assert page_title == "WhowontheIneedathingtodoathingcontract?"

        submit_button = document.xpath('//input[@class="button-save" and @value="Save and continue"]')
        assert len(submit_button) == 1

        # No options should be selected
        labels = document.xpath('//label[@class="selection-button selection-button-radio"]/@class')
        for label_class in labels:
            assert "selected" not in label_class

    def test_award_brief_get_lists_suppliers_who_applied_for_this_brief_alphabetically(self):
        self.login_as_buyer()

        res = self.client.get(self.url.format(brief_id=1234))

        assert self.data_api_client.find_brief_responses.call_args == mock.call(
            1234, status="submitted,pending-awarded"
        )

        document = html.fromstring(res.get_data(as_text=True))
        for i, brief_response in enumerate([(2, 'Aobbins'), (90, 'Bobbins'), (4444, 'Cobbins'), (23, 'Dobbins')]):
            input_id = document.xpath('//input[@id="input-brief_response-{}"]/@value'.format(i + 1))[0]
            assert int(input_id) == brief_response[0]
            label = document.xpath('//label[@for="input-brief_response-{}"]'.format(i+1))[0]
            assert self._strip_whitespace(label.text_content()) == brief_response[1]

    def test_award_brief_get_populates_form_with_a_previously_chosen_brief_response(self):
        self.data_api_client.find_brief_responses.return_value = {
            "briefResponses": [
                {"id": 23, "supplierName": "Dobbins"},
                {"id": 4444, "supplierName": "Cobbins"},
                {"id": 2, "supplierName": "Aobbins"},
                {"id": 90, "supplierName": "Bobbins", "awardDetails": {"pending": True}},
            ]
        }

        self.login_as_buyer()

        res = self.client.get(self.url.format(brief_id=1234))
        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        selected_label_class = document.xpath('//label[@for="input-brief_response-2"]/@class')[0]
        assert "selected" in selected_label_class

        assert self.data_api_client.find_brief_responses.call_args == mock.call(
            1234, status="submitted,pending-awarded"
        )

    def test_award_brief_get_redirects_to_login_if_not_authenticated(self):
        target_url = self.url.format(brief_id=1234)
        res = self.client.get(target_url)
        assert res.status_code == 302
        assert res.location == 'http://localhost/user/login?next={}'.format(target_url.replace('/', '%2F'))

    def test_award_brief_get_returns_404_if_brief_not_closed(self):
        brief_stub = api_stubs.brief(lot_slug="digital-outcomes", status='live')
        self.data_api_client.get_brief.return_value = brief_stub
        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234))
        assert res.status_code == 404

    @mock.patch('app.main.views.buyers.is_brief_correct')
    def test_award_brief_get_returns_404_if_brief_not_correct(self, is_brief_correct):
        is_brief_correct.return_value = False

        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234))
        assert res.status_code == 404

    def test_award_brief_redirects_to_brief_responses_page_if_no_suppliers_applied(self):
        self.data_api_client.find_brief_responses.return_value = {"briefResponses": []}
        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234))
        assert res.status_code == 302
        assert "/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/1234/responses" in res.location  # noqa

    def test_award_brief_post_raises_400_if_required_fields_not_filled(self):
        self.login_as_buyer()
        res = self.client.post(self.url.format(brief_id=1234), data={})
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        error_span = document.xpath('//span[@id="error-brief_response"]')[0]
        assert self._strip_whitespace(error_span.text_content()) == "Youneedtoanswerthisquestion."

    def test_award_brief_post_raises_400_if_form_not_valid(self):
        self.login_as_buyer()
        # Not a valid choice on the AwardedBriefResponseForm list
        res = self.client.post(self.url.format(brief_id=1234), data={'brief_response': 999})
        document = html.fromstring(res.get_data(as_text=True))

        assert res.status_code == 400
        error_span = document.xpath('//span[@id="error-brief_response"]')[0]
        assert self._strip_whitespace(error_span.text_content()) == "Notavalidchoice"

    def test_award_brief_post_valid_form_calls_api_and_redirects_to_next_question(self):
        self.data_api_client.update_brief_award_brief_response.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists-2',
            status='closed',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )
        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.post(self.url.format(brief_id=1234), data={'brief_response': 2})

            assert self.data_api_client.update_brief_award_brief_response.call_args == mock.call(
                u'1234', 2, "buyer@email.com"
            )
            assert res.status_code == 302
            assert "/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/1234/award/2/contract-details" in res.location  # noqa

    def test_award_brief_post_raises_500_on_api_error_and_displays_generic_error_message(self):
        self.data_api_client.update_brief_award_brief_response.side_effect = HTTPError(
            mock.Mock(status_code=500),
            {"title": "BriefResponse cannot be awarded for this Brief"}
        )

        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.post(self.url.format(brief_id=1234), data={'brief_response': 2})
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 500
            error_span = document.xpath('//h1')[0]
            assert self._strip_whitespace(error_span.text_content()) == "Sorry,we'reexperiencingtechnicaldifficulties"


class TestAwardBriefDetails(BaseApplicationTest):
    url = "/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/{brief_id}/award/{brief_response_id}/contract-details"  # noqa

    def setup_method(self, method):
        super(TestAwardBriefDetails, self).setup_method(method)

        self.data_api_client_patch = mock.patch('app.main.views.buyers.data_api_client', autospec=True)
        self.data_api_client = self.data_api_client_patch.start()

        self.data_api_client.get_framework.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists-2',
            status='live',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True),
            ]
        )

        self.data_api_client.get_brief.return_value = api_stubs.brief(
            framework_slug='digital-outcomes-and-specialists-2', lot_slug="digital-outcomes", status='closed'
        )
        self.data_api_client.get_brief_response.return_value = {
            "briefResponses": {
                "id": 5678,
                "briefId": 1234,
                "status": "pending-awarded",
                "supplierName": "BananaCorp",
                "awardDetails": {"pending": True}
            }
        }

    def teardown_method(self, method):
        self.data_api_client_patch.stop()
        super(TestAwardBriefDetails, self).teardown_method(method)

    def _setup_api_error_response(self, error_json):
        self.data_api_client.update_brief_award_details.side_effect = HTTPError(mock.Mock(status_code=400), error_json)

    def test_award_brief_details_200s_with_correct_default_content(self):
        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234, brief_response_id=5678))

        assert res.status_code == 200
        document = html.fromstring(res.get_data(as_text=True))
        self.assert_breadcrumbs(res, extra_breadcrumbs=[
            (
                'I need a thing to do a thing',
                '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/1234'
            )
        ])

        page_title = self._strip_whitespace(document.xpath('//h1')[0].text_content())
        assert page_title == "TellusaboutyourcontractwithBananaCorp"

        submit_button = document.xpath('//input[@class="button-save" and @value="Submit"]')
        assert len(submit_button) == 1

        secondary_link_text = document.xpath('//div[@class="secondary-action-link"]//a[1]')[0]
        assert secondary_link_text.text_content() == "Back to previous page"

        secondary_link = document.xpath('//div[@class="secondary-action-link"]//a[1]/@href')[0]
        assert secondary_link == \
            '/buyers/frameworks/digital-outcomes-and-specialists-2/requirements/digital-outcomes/1234/award-contract'

    def test_award_brief_details_post_valid_form_calls_api_and_redirects(self):
        self.data_api_client.update_brief_award_details.return_value = api_stubs.framework(
            slug='digital-outcomes-and-specialists-2',
            status='awarded',
            lots=[
                api_stubs.lot(slug='digital-outcomes', allows_brief=True)
            ]
        )
        with self.app.app_context():
            self.login_as_buyer()
            res = self.client.post(
                self.url.format(brief_id=1234, brief_response_id=5678),
                data={
                    "awardedContractStartDate-day": "31",
                    "awardedContractStartDate-month": "12",
                    "awardedContractStartDate-year": "2020",
                    "awardedContractValue": "88.84"
                }
            )

            assert self.data_api_client.update_brief_award_details.call_args == mock.call(
                '1234', '5678',
                {'awardedContractStartDate': "2020-12-31", "awardedContractValue": "88.84"},
                updated_by="buyer@email.com"
            )
            assert res.status_code == 302
            assert res.location == "http://localhost/buyers"
            self.assert_flashes("updated-brief")

    @mock.patch('app.main.views.buyers.is_brief_correct')
    def test_award_brief_details_raises_400_if_brief_not_correct(self, is_brief_correct):
        is_brief_correct.return_value = False
        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234, brief_response_id=5678))
        assert res.status_code == 404

    @pytest.mark.parametrize('status', ['awarded', 'submitted', 'draft'])
    def test_award_brief_details_raises_404_if_brief_response_not_pending(self, status):
        self.data_api_client.get_brief_response.return_value["briefResponses"]["status"] = status

        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234, brief_response_id=5678))
        assert res.status_code == 404

    def test_award_brief_details_raises_404_if_brief_response_not_related_to_brief(self):
        """Fake brief_response, as if the user has changed the brief_response.id in the url."""
        self.data_api_client.get_brief_response.return_value['briefResponses']['briefId'] = 9

        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=1234, brief_response_id=99))
        assert res.status_code == 404

    def test_award_brief_details_raises_404_if_brief_not_related_to_brief_response(self):
        """Fake brief, as if the user has changed the brief_id in the url."""
        self.data_api_client.get_brief.return_value['briefs']['id'] = 9

        self.login_as_buyer()
        res = self.client.get(self.url.format(brief_id=9, brief_response_id=5678))
        assert res.status_code == 404

    def _assert_masthead(self, document):
        masthead_error_links = document.xpath('//a[@class="validation-masthead-link"]')
        assert masthead_error_links[0].text_content() == "What's the start date?"
        assert masthead_error_links[1].text_content() == "What's the value?"

    def test_award_brief_details_post_raises_400_if_required_fields_not_filled(self):
        with self.app.app_context():
            self._setup_api_error_response({
                "awardedContractValue": "answer_required",
                "awardedContractStartDate": "answer_required"
            })
            self.login_as_buyer()
            res = self.client.post(self.url.format(brief_id=1234, brief_response_id=5678), data={})
            document = html.fromstring(res.get_data(as_text=True))

            assert res.status_code == 400
            self._assert_masthead(document)
            error_spans = document.xpath('//span[@class="validation-message"]')
            assert self._strip_whitespace(error_spans[0].text_content()) == "Youneedtoanswerthisquestion."
            assert self._strip_whitespace(error_spans[1].text_content()) == "Youneedtoanswerthisquestion."

    def test_award_brief_details_post_raises_400_and_displays_error_messages_and_prefills_fields_if_invalid_data(self):
        with self.app.app_context():
            self._setup_api_error_response({
                "awardedContractStartDate": "invalid_format",
                "awardedContractValue": "not_money_format"
            })
            self.login_as_buyer()

            res = self.client.post(
                self.url.format(brief_id=1234, brief_response_id=5678),
                data={
                    "awardedContractValue": "incorrect",
                    "awardedContractStartDate-day": "x",
                    "awardedContractStartDate-month": "y",
                    "awardedContractStartDate-year": "z"
                }
            )

            assert res.status_code == 400
            document = html.fromstring(res.get_data(as_text=True))

            self._assert_masthead(document)

            # Individual error messages
            error_spans = document.xpath('//span[@class="validation-message"]')
            assert self._strip_whitespace(error_spans[0].text_content()) == "Youranswermustbeavaliddate."
            assert self._strip_whitespace(error_spans[1].text_content()) == \
                "Valuemustbeinnumbersanddecimalpointsonly,forexample99.95."

            # Prefilled form input
            assert document.xpath('//input[@id="input-awardedContractValue"]/@value')[0] == "incorrect"
            assert document.xpath('//input[@id="input-awardedContractStartDate-day"]/@value')[0] == "x"
            assert document.xpath('//input[@id="input-awardedContractStartDate-month"]/@value')[0] == "y"
            assert document.xpath('//input[@id="input-awardedContractStartDate-year"]/@value')[0] == "z"

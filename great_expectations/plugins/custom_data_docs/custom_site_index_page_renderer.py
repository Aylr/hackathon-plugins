import datetime
import json
import logging
import traceback

import tzlocal
from dateutil.parser import parse
from great_expectations.render.renderer import CallToActionRenderer, SiteIndexPageRenderer
from great_expectations.render.renderer.renderer import Renderer

from great_expectations.render.types import (
    RenderedBootstrapTableContent,
    RenderedDocumentContent,
    RenderedHeaderContent,
    RenderedSectionContent,
    RenderedStringTemplateContent,
    RenderedTabsContent,
)

logger = logging.getLogger(__name__)


class CustomSiteIndexPageRenderer(SiteIndexPageRenderer):
    @classmethod
    def render(cls, index_links_dict):
        sections = []
        cta_object = index_links_dict.pop("cta_object", None)

        try:
            content_blocks = []
            # site name header
            site_name_header_block = RenderedHeaderContent(
                **{
                    "content_block_type": "header",
                    "header": RenderedStringTemplateContent(
                        **{
                            "content_block_type": "string_template",
                            "string_template": {
                                "template": "$title_prefix | $site_name",
                                "params": {
                                    "site_name": index_links_dict.get("site_name"),
                                    "title_prefix": "Data Docs",
                                },
                                "styling": {
                                    "params": {"title_prefix": {"tag": "strong"}}
                                },
                            },
                        }
                    ),
                    "styling": {
                        "classes": ["col-12", "ge-index-page-site-name-title"],
                        "header": {"classes": ["alert", "alert-secondary"]},
                    },
                }
            )
            content_blocks.append(site_name_header_block)

            tabs = []

            if index_links_dict.get("validations_links"):
                tabs.append(
                    {
                        "tab_name": "Validation Results",
                        "tab_content": cls._generate_validation_results_link_table(
                            index_links_dict
                        ),
                    }
                )
            if index_links_dict.get("profiling_links"):
                tabs.append(
                    {
                        "tab_name": "Profiling Results",
                        "tab_content": cls._generate_profiling_results_link_table(
                            index_links_dict
                        ),
                    }
                )
            if index_links_dict.get("expectations_links"):
                tabs.append(
                    {
                        "tab_name": "Expectation Suites",
                        "tab_content": cls._generate_expectation_suites_link_table(
                            index_links_dict
                        ),
                    }
                )

            tabs_content_block = RenderedTabsContent(
                **{
                    "tabs": tabs,
                    "styling": {"classes": ["col-12", "ge-index-page-tabs-container"], },
                }
            )

            content_blocks.append(tabs_content_block)

            section = RenderedSectionContent(
                **{
                    "section_name": index_links_dict.get("site_name"),
                    "content_blocks": content_blocks,
                }
            )
            sections.append(section)

            index_page_document = RenderedDocumentContent(
                **{
                    "renderer_type": "SiteIndexPageRenderer",
                    "utm_medium": "index-page",
                    "sections": sections,
                }
            )

            if cta_object:
                index_page_document.cta_footer = CallToActionRenderer.render(cta_object)

            return index_page_document

        except Exception as e:
            exception_message = f"""\
    An unexpected Exception occurred during data docs rendering.  Because of this error, certain parts of data docs will \
    not be rendered properly and/or may not appear altogether.  Please use the trace, included in this message, to \
    diagnose and repair the underlying issue.  Detailed information follows:
                """
            exception_traceback = traceback.format_exc()
            exception_message += (
                f'{type(e).__name__}: "{str(e)}".  Traceback: "{exception_traceback}".'
            )
            logger.error(exception_message, e, exc_info=True)

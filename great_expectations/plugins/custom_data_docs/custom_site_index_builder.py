import logging
import os
import traceback
from collections import OrderedDict

import great_expectations.exceptions as exceptions
from great_expectations.core import nested_update
from great_expectations.data_context.store.html_site_store import (
    HtmlSiteStore,
    SiteSectionIdentifier,
)
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)
from great_expectations.data_context.util import instantiate_class_from_config

from great_expectations.render.renderer.site_builder import (
    DefaultSiteIndexBuilder
)

class CustomSiteIndexBuilder(DefaultSiteIndexBuilder):
    def __init__(self,
        name,
        site_name,
        data_context,
        target_store,
        custom_styles_directory=None,
        custom_views_directory=None,
        show_how_to_buttons=True,
        validation_results_limit=None,
        renderer=None,
        view=None,
        data_context_id=None,
        source_stores=None,
        **kwargs):
         super().__init__(
         name,
         site_name,
         data_context,
         target_store,
         custom_styles_directory,
         custom_views_directory,
         show_how_to_buttons,
         validation_results_limit,
         renderer,
         view,
         data_context_id,
         source_stores,
         **kwargs
            )

    def build(self):
        logger.debug("DefaultSiteIndexBuilder.build")

        expectation_suite_keys = [
            ExpectationSuiteIdentifier.from_tuple(expectation_suite_tuple)
            for expectation_suite_tuple in self.target_store.store_backends[
                ExpectationSuiteIdentifier
            ].list_keys()
        ]
        validation_and_profiling_result_keys = [
            ValidationResultIdentifier.from_tuple(validation_result_tuple)
            for validation_result_tuple in self.target_store.store_backends[
                ValidationResultIdentifier
            ].list_keys()
        ]
        profiling_result_keys = [
            validation_result_key
            for validation_result_key in validation_and_profiling_result_keys
            if validation_result_key.run_id.run_name == "profiling"
        ]
        validation_result_keys = [
            validation_result_key
            for validation_result_key in validation_and_profiling_result_keys
            if validation_result_key.run_id.run_name != "profiling"
        ]
        validation_result_keys = sorted(
            validation_result_keys, key=lambda x: x.run_id.run_time, reverse=True
        )

        if self.validation_results_limit:
            validation_result_keys = validation_result_keys[
                : self.validation_results_limit
            ]

        index_links_dict = OrderedDict()
        index_links_dict["site_name"] = self.site_name

        if self.show_how_to_buttons:
            index_links_dict["cta_object"] = self.get_calls_to_action()

        for expectation_suite_key in expectation_suite_keys:
            self.add_resource_info_to_index_links_dict(
                index_links_dict=index_links_dict,
                expectation_suite_name=expectation_suite_key.expectation_suite_name,
                section_name="expectations",
            )

        for profiling_result_key in profiling_result_keys:
            try:
                validation = self.data_context.get_validation_result(
                    batch_identifier=profiling_result_key.batch_identifier,
                    expectation_suite_name=profiling_result_key.expectation_suite_identifier.expectation_suite_name,
                    run_id=profiling_result_key.run_id,
                    validations_store_name=self.source_stores.get("profiling"),
                )

                batch_kwargs = validation.meta.get("batch_kwargs", {})

                self.add_resource_info_to_index_links_dict(
                    index_links_dict=index_links_dict,
                    expectation_suite_name=profiling_result_key.expectation_suite_identifier.expectation_suite_name,
                    section_name="profiling",
                    batch_identifier=profiling_result_key.batch_identifier,
                    run_id=profiling_result_key.run_id,
                    run_time=profiling_result_key.run_id.run_time,
                    run_name=profiling_result_key.run_id.run_name,
                    asset_name=batch_kwargs.get("data_asset_name"),
                    batch_kwargs=batch_kwargs,
                )
            except Exception:
                error_msg = "Profiling result not found: {0:s} - skipping".format(
                    str(profiling_result_key.to_tuple())
                )
                logger.warning(error_msg)

        for validation_result_key in validation_result_keys:
            try:
                validation = self.data_context.get_validation_result(
                    batch_identifier=validation_result_key.batch_identifier,
                    expectation_suite_name=validation_result_key.expectation_suite_identifier.expectation_suite_name,
                    run_id=validation_result_key.run_id,
                    validations_store_name=self.source_stores.get("validations"),
                )

                validation_success = validation.success
                batch_kwargs = validation.meta.get("batch_kwargs", {})

                self.add_resource_info_to_index_links_dict(
                    index_links_dict=index_links_dict,
                    expectation_suite_name=validation_result_key.expectation_suite_identifier.expectation_suite_name,
                    section_name="validations",
                    batch_identifier=validation_result_key.batch_identifier,
                    run_id=validation_result_key.run_id,
                    validation_success=validation_success,
                    run_time=validation_result_key.run_id.run_time,
                    run_name=validation_result_key.run_id.run_name,
                    asset_name=batch_kwargs.get("data_asset_name"),
                    batch_kwargs=batch_kwargs,
                )
            except Exception:
                error_msg = "Validation result not found: {0:s} - skipping".format(
                    str(validation_result_key.to_tuple())
                )
                logger.warning(error_msg)

        self.add_report_info_to_index_links_dict(index_links_dict, validation_result_keys)

        try:
            rendered_content = self.renderer_class.render(index_links_dict)
            viewable_content = self.view_class.render(
                rendered_content,
                data_context_id=self.data_context_id,
                show_how_to_buttons=self.show_how_to_buttons,
            )
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

        return (self.target_store.write_index_page(viewable_content), index_links_dict)


    def add_report_info_to_index_links_dict(self, index_links_dict, validation_result_keys):
        pass

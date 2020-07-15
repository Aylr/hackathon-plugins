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
    SiteBuilder
)

class CustomSiteIndexBuilder(SiteBuilder):
    def __init__(
        self,
        data_context,
        store_backend,
        site_name=None,
        site_index_builder=None,
        show_how_to_buttons=True,
        site_section_builders=None,
        runtime_environment=None,
        **kwargs,
    ):
        self.site_name = site_name
        self.data_context = data_context
        self.store_backend = store_backend
        self.show_how_to_buttons = show_how_to_buttons

        usage_statistics_config = data_context.anonymous_usage_statistics
        data_context_id = None
        if (
            usage_statistics_config
            and usage_statistics_config.enabled
            and usage_statistics_config.data_context_id
        ):
            data_context_id = usage_statistics_config.data_context_id

        self.data_context_id = data_context_id

        # set custom_styles_directory if present
        custom_styles_directory = None
        plugins_directory = data_context.plugins_directory
        if plugins_directory and os.path.isdir(
            os.path.join(plugins_directory, "custom_data_docs", "styles")
        ):
            custom_styles_directory = os.path.join(
                plugins_directory, "custom_data_docs", "styles"
            )

        # set custom_views_directory if present
        custom_views_directory = None
        if plugins_directory and os.path.isdir(
            os.path.join(plugins_directory, "custom_data_docs", "views")
        ):
            custom_views_directory = os.path.join(
                plugins_directory, "custom_data_docs", "views"
            )

        if site_index_builder is None:
            site_index_builder = {"class_name": "CustomSiteIndexBuilder"}

        # The site builder is essentially a frontend store. We'll open up
        # three types of backends using the base
        # type of the configuration defined in the store_backend section

        self.target_store = HtmlSiteStore(
            store_backend=store_backend, runtime_environment=runtime_environment
        )

        default_site_section_builders_config = {
            "expectations": {
                "class_name": "DefaultSiteSectionBuilder",
                "source_store_name": data_context.expectations_store_name,
                "renderer": {"class_name": "ExpectationSuitePageRenderer"},
            },
            "validations": {
                "class_name": "DefaultSiteSectionBuilder",
                "source_store_name": data_context.validations_store_name,
                "run_name_filter": {"ne": "profiling"},
                "renderer": {"class_name": "ValidationResultsPageRenderer"},
                "validation_results_limit": site_index_builder.get(
                    "validation_results_limit"
                ),
            },
            "profiling": {
                "class_name": "DefaultSiteSectionBuilder",
                "source_store_name": data_context.validations_store_name,
                "run_name_filter": {"eq": "profiling"},
                "renderer": {"class_name": "ProfilingResultsPageRenderer"},
            },
            "metrics": {
                "class_name": "DefaultSiteSectionBuilder",
                # "source_store_name": data_context.validations_store_name,
                "renderer": {"class_name": "MetricsResultsPageRenderer"},
            },
        }

        if site_section_builders is None:
            site_section_builders = default_site_section_builders_config
        else:
            site_section_builders = nested_update(
                default_site_section_builders_config, site_section_builders
            )
        self.site_section_builders = {}
        for site_section_name, site_section_config in site_section_builders.items():
            if not site_section_config or site_section_config in [
                "0",
                "None",
                "False",
                "false",
                "FALSE",
                "none",
                "NONE",
            ]:
                continue
            module_name = (
                site_section_config.get("module_name")
                or "great_expectations.render.renderer.site_builder"
            )
            self.site_section_builders[
                site_section_name
            ] = instantiate_class_from_config(
                config=site_section_config,
                runtime_environment={
                    "data_context": data_context,
                    "target_store": self.target_store,
                    "custom_styles_directory": custom_styles_directory,
                    "custom_views_directory": custom_views_directory,
                    "data_context_id": self.data_context_id,
                    "show_how_to_buttons": self.show_how_to_buttons,
                },
                config_defaults={"name": site_section_name, "module_name": module_name},
            )
            if not self.site_section_builders[site_section_name]:
                raise exceptions.ClassInstantiationError(
                    module_name=module_name,
                    package_name=None,
                    class_name=site_section_config["class_name"],
                )

        module_name = (
            site_index_builder.get("module_name")
            or "great_expectations.render.renderer.site_builder"
        )
        class_name = site_index_builder.get("class_name") or "CustomSiteIndexBuilder"
        self.site_index_builder = instantiate_class_from_config(
            config=site_index_builder,
            runtime_environment={
                "data_context": data_context,
                "custom_styles_directory": custom_styles_directory,
                "custom_views_directory": custom_views_directory,
                "show_how_to_buttons": self.show_how_to_buttons,
                "target_store": self.target_store,
                "site_name": self.site_name,
                "data_context_id": self.data_context_id,
                "source_stores": {
                    section_name: section_config.get("source_store_name")
                    for (section_name, section_config) in site_section_builders.items()
                },
            },
            config_defaults={
                "name": "site_index_builder",
                "module_name": module_name,
                "class_name": class_name,
            },
        )
        if not self.site_index_builder:
            raise exceptions.ClassInstantiationError(
                module_name=module_name,
                package_name=None,
                class_name=site_index_builder["class_name"],
            )

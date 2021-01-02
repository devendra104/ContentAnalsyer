import ast
import filecmp
import json
import os
import re
import shutil
from difflib import Differ

import yaml

from utils.xls_report_builder import XlsReportBuilder
from utils.xls_report_propertes import TestAnalysisProperties


class ExistenceTestFailureAnalysis:
    def __init__(self):
        self.basepath = os.path.abspath('.')
        self.prop_obj = TestAnalysisProperties()
        self.config_details = self.yaml_to_dict_converter("config.yml", "ReportConfig")
        self.result_file_path = os.path.abspath(f'report/{self.config_details["result_file"]}')
        self.pre_post_data_map = {
            'pre_data': {
                'pre_api': [
                    f"{self.basepath}/preupgrade_api",
                    f"{self.basepath}/pre_upgrade_data_api",
                    "api"
                ],
                'pre_cli': [
                    f"{self.basepath}/preupgrade_cli",
                    f"{self.basepath}/pre_upgrade_data_cli",
                    "cli"
                ],
            },
            'post_data': {
                'post_api': [
                    f"{self.basepath}/postupgrade_api",
                    f"{self.basepath}/post_upgrade_data_api",
                    "api"
                ],
                'post_cli': [
                    f"{self.basepath}/postupgrade_cli",
                    f"{self.basepath}/post_upgrade_data_cli",
                    "cli"
                ],
            }
        }

    def run(self, component_type, component, attribute, pre_post_data):
        """
        This method is used to trigger the main method and perform the cleanup of all
        properties
        :return:
        """
        if component_type == "Template":
            self.xls_data_field_updater(component_type, component, attribute, pre_post_data)
            self.prop_obj.rows_no += 1
        else:
            for pre_post in pre_post_data:
                self.xls_data_field_updater(component_type, component, attribute, pre_post)
                self.prop_obj.rows_no += 1

    def xls_sheet_header(self, component_type):
        """
        This method is used to create a new xlsx sheet and added the header.
        :param component_type:
        :return:
        """
        if self.prop_obj.new_sheets:
            self.prop_obj.new_sheets = False
            self.prop_obj.rows_no = 1
            self.prop_obj.count_index += 1

        if self.prop_obj.rows_no == 1:
            # This statement is used to create an empty xlsx sheet.
            if self.prop_obj.count_index == 1:
                xls_report = XlsReportBuilder(self.result_file_path, XlsReportBuilder.MODENEW)
                xls_report.open_work_book(component_type, self.result_file_path)

            # This statement is used to add a new component sheet in the existing xlsx sheet
            if not self.prop_obj.new_sheet:
                xlsstyle = XlsReportBuilder.xls_sheet_style("header")
                xls_report = XlsReportBuilder(self.result_file_path,
                                              XlsReportBuilder.MODEWRITE)
            else:
                xlsstyle = XlsReportBuilder.xls_sheet_style("data_field")
                xls_report = XlsReportBuilder(self.result_file_path,
                                              XlsReportBuilder.MODEAPPEND)
            xls_report.open_work_book(component_type, self.result_file_path,
                                      self.prop_obj.count_index)
            if component_type == "Template":
                common_config_data = self.config_details["template_report_header"]
                new_added_field = [item.strip(":") for item in
                                   self.config_details["specific_data_selection_field"][
                                       component_type]]
                all_template_possible_field = common_config_data + new_added_field
                xls_report.write_row(1, 1, all_template_possible_field,
                                     xlsstyle, self.config_details[
                                         "template_column_variation_index"])
            else:
                xls_report.write_row(1, 1, self.config_details["nontemplate_report_header"],
                                     xlsstyle, self.config_details[
                                         "nontemplate_column_variation_index"])
            xls_report.workbook.save(self.result_file_path)
            xls_report.close_work_book()
            self.prop_obj.rows_no = self.prop_obj.rows_no + 1

    def xls_data_field_updater(self, component_type, component, attribute, pre_post):
        """
        This method is used to update the xls sheet based on the provided data
        :param component_type: Component type like CLI, API, Template etc
        :param component: component is the component_types entities like activation_key, gpg,
        domain etc
        :param attribute: each component has some entities like name, id, value etc.
        :param pre_post:
        :return:
        """
        self.xls_sheet_header(component_type)
        xlsstyle = XlsReportBuilder.xls_sheet_style("data_field")
        xls_report_content = [component_type, component, attribute]
        if component_type != "Template":
            for content in pre_post:
                ppost = pre_post[content]
                xls_report_content.append(ppost)
        else:
            list_of_data = list()
            common_config_data = self.config_details["template_report_header"]
            new_added_field = [item.strip(":") for item in
                               self.config_details[
                                   "specific_data_selection_field"][component_type]]
            all_template_possible_field = common_config_data + new_added_field
            for item in all_template_possible_field:
                list_of_data.append(pre_post[item])
            xls_report_content = list_of_data
            # xls_report_content.append(pre_post)
        self.result_updater(component_type, self.prop_obj.row_no, xls_report_content,
                            self.prop_obj.count_index, xlsstyle, [3, 4, 5])

    def result_updater(self, component_type, row_number, data_list, index, xlsstyle,
                       index_list):
        xls_report = XlsReportBuilder(self.result_file_path, XlsReportBuilder.MODEAPPEND)
        xls_report.open_work_book(component_type, self.result_file_path, index)
        column_number = 1
        for content in data_list:
            xls_report.write_row(row_number, column_number, "{}".format(content), xlsstyle,
                                 index_list)
            column_number += 1
        xls_report.workbook.save(self.result_file_path)
        XlsReportBuilder.cell_alignment(self.result_file_path, index_list)

    def file_reader(self, file):
        """
        This method is used to read the data from file and saved it in well formatted
        dictionary.
        :param file:
        :return:
        """
        with open("{}".format(file)) as fd_pre:
            non_formated_data = ast.literal_eval(json.dumps(fd_pre.readlines()))
        formated_dict = ast.literal_eval(non_formated_data[0])
        return formated_dict

    def cli_api_data(self, data, cli_api_data_populated_dir, type_name):
        """
        :param cli_api_data_populated_dir:
        :param type_name:
        :return:
        """
        print(cli_api_data_populated_dir)
        if os.path.isdir(cli_api_data_populated_dir):
            shutil.rmtree(cli_api_data_populated_dir)
        os.mkdir(cli_api_data_populated_dir)

        if type_name == "cli":
            with open(f"{data}") as fd:
                cli_data = fd.readlines()[0]
            for m in ast.literal_eval(cli_data):
                for j in m:
                    fd = open(f"{cli_api_data_populated_dir}/{j}", "w")
                    fd.write(f"{m}")
                    fd.close()
        elif type_name == "api":
            with open(f"{data}") as fd:
                cli_data = fd.readlines()[0]
            for component_dict in json.loads(ast.literal_eval(json.dumps(cli_data))):
                for key in component_dict:
                    fd = open(f"{cli_api_data_populated_dir}/{key}", "w")
                    fd.write(f"{component_dict}")
                    fd.close()

    def pre_data_compare(self, module_name, pre_data, post_data=None):
        """
        This method is used to prepare a variance list by using the pre and post upgraded data.
        :param module_name:
        :param pre_data:
        :param post_data:
        :return:
        """
        common_diff_data = list()
        pre_entity_data = self.file_reader(pre_data)
        post_entity_data = self.file_reader(post_data)
        for item in pre_entity_data:
            for attribute in pre_entity_data[item]:
                status, post_content = self.post_data_compare(module_name,
                                                              post_entity_data,
                                                              attribute)
                if status == 0:
                    pass
                elif status == 1 and post_content:
                    common_diff_data.append(attribute)
                elif status == 1 and not post_content:
                    common_diff_data.append(attribute)
        return common_diff_data

    def post_data_compare(self, module_name, post_entity_data, pre_data_attribute):
        """
        This method is used to collect the variance between pre-upgrades entities attribute
        and post-upgrade entities attribute.
        :param module_name: category of data, it can be CLI, API or Template.
        :param post_entity_data: entity based data like dns, activation-key, domain, os etc.
        :param pre_data_attribute: This is pre data's entities attribute like name, id, value
         etc.
        :return: 0(match) or 1(mismatch) and variance pre data attributes(variance) or
        empty dict(no variance).
        """
        for item in post_entity_data:
            if module_name == "API":
                if pre_data_attribute in post_entity_data[item]:
                    return 0, {}
            elif module_name == "CLI":
                for post_data_attribute in post_entity_data[item]:
                    if post_data_attribute == pre_data_attribute:
                        return 0, {}
                    elif post_data_attribute.values() == pre_data_attribute.values():
                        return 1, post_data_attribute
                    elif set(post_data_attribute.values()).\
                            issubset(set(pre_data_attribute.values())):
                        return 1, post_data_attribute
                    elif set(pre_data_attribute.values()).\
                            issubset(set(post_data_attribute.values())):
                        return 1, post_data_attribute
            return 1, pre_data_attribute

    def attribute_base_comparison(self, post_data, component_name, component_value,
                                  component_common_name, variation_data_list):
        """
        This method is used to compare the variance entities with post upgrades entities that
        helps to know the exact variance.
        :param post_data:
        :param component_name:
        :param component_value:
        :param component_common_name:
        :param variation_data_list:
        :return:
        """
        post_data_sets = self.file_reader(post_data)[component_name]
        not_exist = []
        variance_dict = {}
        for variance in component_value:
            variance_dict[variance] = []
        for variation_data in variation_data_list:
            for post_data in post_data_sets:
                if post_data[component_common_name] == variation_data[component_common_name]:
                    break
            else:
                pre_post_pair = {"pre_data": variation_data, "post_data": "",
                                 "Variation": f"{variation_data[component_common_name]} "
                                 f"key was missing after upgrade"}
                not_exist.append(pre_post_pair)
        for post_data in post_data_sets:
            for variation_data in variation_data_list:
                if post_data[component_common_name] == variation_data[component_common_name]:
                    for component in component_value:
                        if post_data[component] != variation_data[component]:
                            pre_post_pair = {"pre_data": variation_data, "post_data": post_data,
                                             "Variation": f" '{component_name}' "
                                             f"entities attribute '{component}' changed from "
                                             f" '{variation_data[component]}' to "
                                             f"'{post_data[component]}'"}
                            variance_dict[component].append(pre_post_pair)
                    variation_data_list.remove(variation_data)
                    break
        return variance_dict, not_exist

    def data_segregation(self):
        """
        This method is used to segregate all the modules data with component-wise.
        :return:
        """
        for module in self.pre_post_data_map:
            for component in self.pre_post_data_map[module]:
                self.cli_api_data(self.pre_post_data_map[module][component][0],
                                  self.pre_post_data_map[module][component][1],
                                  self.pre_post_data_map[module][component][2]
                                  )

    def yaml_to_dict_converter(self, file_name, file_header):
        """
        This method use to convert the validation_parameter yaml file in to dictionary.
        :return: validation_param
        """
        validation_param = ast.literal_eval(
            json.dumps(
                yaml.load(open(f"{self.basepath}/config/{file_name}"), Loader=yaml.FullLoader)
                [file_header])
        )
        return validation_param

    def deprecation_check(self, component, pre_data, post_data):
        """
        This method is used to check whether the component is deprecated or not.
        :param component:
        :param pre_data:
        :param post_data:
        :return:
        """
        deprecated_items = ["sub-command is deprecated and will be removed in "
                            "one of the future versions", "error: no such sub-command"]
        depricated_list = []
        pre_data_list = self.file_reader(pre_data)
        post_data_list = self.file_reader(post_data)

        def pre_data():
            for pre_dict in pre_data_list[component]:
                return pre_dict

        for post_item_dict in post_data_list[component]:
            for key in post_item_dict:
                for deprecated_item in deprecated_items:
                    if re.search(rf'{deprecated_item}', key):
                        depricated_list.append({'pre': pre_data(), 'post': post_item_dict,
                                                "Variation": f"'{component}' is deprecated"})
                        return depricated_list
        return []

    def specific_data_field_extraction(self, module_name, data_sets):
        """
        :return:
        """
        field_list = self.config_details["specific_data_selection_field"][module_name]
        specific_filed_data = dict()
        for item in data_sets:
            for field in field_list:
                if re.search(rf"^{field.lower()}", item):
                    specific_filed_data[field.strip(":")] = \
                        re.search(rf"^{field.lower()} .*", f'{item}').group().split(
                            f'{field.lower()}')[-1].strip()
        if not specific_filed_data:
            for field in field_list:
                specific_filed_data[field.strip(":")] = "job-template"
        return specific_filed_data

    def post_template_comparison(self, component_type, component_name, pre_data, post_data,
                                 variance_templates):
        """
        This method is used to collect the added and removed content by comparing the variance
        data with post-upgrade data content.
        :param component_type: Module name
        :param component_name: Modules component it could be
        :param pre_data:
        :param post_data:
        :param variance_templates:
        :return:
        """
        def read_template_file(data_file):
            with open(f'{data_file}', 'r') as file_obj:
                return [con.strip() for con in file_obj.readlines()]
        post_data_variance = list()
        for i, j, k in os.walk(f'{pre_data}'):
            for item in k:
                pre_data_file = f"{i}/{item}"
                post_data_file = f"{post_data}/{item}"
                pre_content = read_template_file(pre_data_file)
                with open(f'{post_data_file}', "r") as fd:
                    content = fd.readlines()
                post_content = [con.strip() for con in content]
                if pre_data_file in variance_templates[component_name]:
                    diff = Differ()
                    difference = list(diff.compare(pre_content, post_content))
                    added_elements = [added for added in difference if added.startswith('+')]
                    removed_elements = [added for added in difference if added.startswith('-')]
                    if added_elements or removed_elements:
                        specific_field_data = self.specific_data_field_extraction(
                            component_type, pre_content)
                        variance_data = {"Template_File_Name": f'{pre_data_file}',
                                         "Added": added_elements, "Removed": removed_elements}
                        for kind in self.config_details["specific_data_selection_field"][
                                component_type]:
                            variance_data[kind.strip(":")] = specific_field_data[
                                kind.strip(":")]
                        post_data_variance.append(variance_data)
        return post_data_variance

    def missing_template(self, component_name, pre_data, post_data):
        """
        This method is used to check the missing template.
        :param component_name:
        :param pre_data:
        :param post_data:
        :return:
        """
        missing_template = {component_name: []}
        for i, j, k in os.walk(f'{pre_data}'):
            for item in k:
                pre_data_file = f"{i}/{item}"
                post_data_file = f"{post_data}/{item}"
                if not (os.path.isfile(pre_data_file) and os.path.isfile(post_data_file)):
                    missing_template[component_name].append(pre_data_file)
        return missing_template

    def variance_template(self, component_name, pre_data, post_data):
        """
        This method is used to collect the variance between pre_upgraded data with
        post_upgraded data
        :param component_name: name of the template type, it could be job_template,
        provisioning etc
        :param pre_data: all the data file for the specific component before upgrade.
        :param post_data:all the data file for the specific component after upgrade.
        :return: dictionary of component variance.

        """
        variance_template_file = {component_name: []}
        for i, j, k in os.walk(f'{pre_data}'):
            for item in k:
                pre_data_file = f"{i}/{item}"
                post_data_file = f"{post_data}/{item}"
                if os.path.isfile(pre_data_file) and os.path.isfile(post_data_file):
                    status = filecmp.cmp(pre_data_file, post_data_file)
                    if not status:
                        variance_template_file[component_name].append(pre_data_file)
        return variance_template_file

    def template_report_builder(self, module_name, component_type_data):
        for component_name in component_type_data:
            pre_data = f"{self.basepath}/preupgrade_templates/{component_name}"
            post_data = f"{self.basepath}/postupgrade_templates/{component_name}"
            # missing_templates = self.missing_template(component_name, pre_data, post_data)
            varinace_templates = self.variance_template(component_name, pre_data,
                                                        post_data)
            component_diff = self.post_template_comparison(module_name,
                                                           component_name, pre_data,
                                                           post_data, varinace_templates)
            print("COM diff", component_diff)
            for varinace_map in component_diff:
                varinace_map["Module"] = module_name
                varinace_map["Component"] = component_name
                self.run(module_name, component_name, "Template", varinace_map)

    def cli_api_report_builder(self, module_name, component_type_data):
        for component_name in component_type_data:
            component_name = component_name
            component_attributes = component_type_data[component_name]["component"]
            component_id = component_type_data[component_name]["common-id"]
            if module_name == "CLI":
                # self.new_sheet = True
                pre_data = f"{self.basepath}/pre_upgrade_data_cli/{component_name}"
                post_data = f"{self.basepath}/post_upgrade_data_cli/{component_name}"
            else:
                self.prop_obj.new_sheets = True
                pre_data = f"{self.basepath}/pre_upgrade_data_api/{component_name}"
                post_data = f"{self.basepath}/post_upgrade_data_api/{component_name}"

            if os.path.isfile(pre_data):
                deprication_list = self.deprecation_check(component_name, pre_data, post_data)
                if deprication_list:
                    self.run(module_name, component_name, component_id, deprication_list)
                else:
                    variation_data_list = self.pre_data_compare(module_name, pre_data,
                                                                post_data)
                    variance_data, not_exist = \
                        self.attribute_base_comparison(post_data, component_name,
                                                       component_attributes, component_id,
                                                       variation_data_list)
                    self.run(module_name, component_name, component_id, not_exist)
                    for attribute in component_attributes:
                        self.run(module_name, component_name, attribute,
                                 variance_data[attribute])

    def report_builder(self):
        for component_type in self.config_details["module_name"]:
            component_type_data = self.yaml_to_dict_converter(
                self.config_details["modules_entities_config_file"],
                component_type)
            if component_type == "Template":
                self.prop_obj.new_sheets = True
                self.template_report_builder(component_type, component_type_data)
            else:
                self.cli_api_report_builder(component_type, component_type_data)

    def __del__(self):
        """
        :return:
        """
        del self.prop_obj.rows_no
        for module in self.pre_post_data_map:
            for component in self.pre_post_data_map[module]:
                shutil.rmtree(self.pre_post_data_map[module][component][1])

# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.fixtures import sync_fixtures


def execute():
	frappe.reload_doc("press", "doctype", "app")
	frappe.reload_doc("press", "doctype", "app_source")
	frappe.reload_doc("press", "doctype", "frappe_version")
	sync_fixtures("press")
	frappe.reload_doc("press", "doctype", "app_source_version")
	frappe.reload_doc("press", "doctype", "app_release")
	frappe.reload_doc("press", "doctype", "app_release_difference")
	frappe.reload_doc("press", "doctype", "release_group_app")
	frappe.reload_doc("press", "doctype", "bench_app")
	frappe.reload_doc("press", "doctype", "deploy_candidate_app")
	apps = frappe.get_all("App", "*")
	for app in apps:
		versions = set(frappe.get_all("Release Group", {"app": app.name}, pluck="version"))
		if versions:
			source = {
				"doctype": "App Source",
				"app": app.name,
				"app_title": app.title,
				"frappe": app.frappe,
				"enabled": app.enabled,
				"repository_url": app.url,
				"repository": app.repo,
				"repository_owner": app.repo_owner,
				"branch": app.branch,
				"github_installation_id": app.installation,
				"public": app.public,
				"team": app.team,
				"versions": [{"version": version} for version in versions],
			}
			source = frappe.get_doc(source)
			source.set_new_name()
			source.set_parent_in_children()
			source.db_insert()

			for child in source.get_all_children():
				child.db_insert()

			frappe.db.set_value("App Release", {"app": app.name}, "source", source.name)
			frappe.db.set_value("Bench App", {"app": app.name}, "source", source.name)
			frappe.db.set_value("Deploy Candidate App", {"app": app.name}, "source", source.name)
			frappe.db.set_value("Release Group App", {"app": app.name}, "source", source.name)


def delete():
	frappe.db.set_value("App Release", {"cloned": False}, "source", None)
	for difference in frappe.get_all("App Release Difference"):
		frappe.delete_doc("App Release Difference", difference.name)
	for source in frappe.get_all("App Source"):
		frappe.delete_doc("App Source", source.name)
	frappe.db.delete(
		"Patch Log", {"patch": "press.patches.v0_0_1.create_app_source_from_app"}
	)

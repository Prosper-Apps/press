// Copyright (c) 2020, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deploy Candidate', {
	refresh: function (frm) {
		frm.fields_dict['apps'].grid.get_field('app').get_query = function (doc) {
			return {
				query: 'press.press.doctype.deploy_candidate.deploy_candidate.desk_app',
				filters: { release_group: doc.group },
			};
		};
		set_handler(
			frm,
			'Complete',
			'build',
			{ no_push: false, no_build: false, no_cache: false },
			'Build',
		);
		set_handler(
			frm,
			'Generate Context',
			'build',
			{ no_push: true, no_build: true, no_cache: false },
			'Build',
		);
		set_handler(
			frm,
			'Without Cache',
			'build',
			{ no_push: false, no_build: false, no_cache: true },
			'Build',
		);
		set_handler(
			frm,
			'Without Push',
			'build',
			{ no_push: true, no_build: false, no_cache: false },
			'Build',
		);
		set_handler(
			frm,
			'Schedule Build and Deploy',
			'schedule_build_and_deploy',
			{ run_now: false },
			'Deploy',
		);
	},
});

function set_handler(frm, label, method, args, group) {
	const handler = get_handler(frm, method, args);
	frm.add_custom_button(label, handler, group);
}

function get_handler(frm, method, args) {
	return async function handler() {
		const { message: data } = await frm.call({ method, args, doc: frm.doc });

		if (data?.error) {
			frappe.msgprint({
				title: 'Action Failed',
				indicator: 'yellow',
				message: data.message,
			});
			return;
		}

		if (method.endsWith('redeploy') && data?.message) {
			frappe.msgprint({
				title: 'Redeploy Triggered',
				indicator: 'green',
				message: __(`Duplicate {0} created and redeploy triggered.`, [
					`<a href="/app/deploy-candidate/${data?.message}">Deploy Candidate</a>`,
				]),
			});
		}

		if (
			(method === 'build' || method === 'schedule_build_and_deploy') &&
			data
		) {
			frappe.msgprint({
				title: 'Deploy Candidate Build Created',
				indicator: 'green',
				message: __(`New {0} has been created`, [
					`<a href="/app/deploy-candidate-build/${data.message.message}">Deploy Candidate Build</a>`,
				]),
			});
		}

		if (method === 'deploy' && data) {
			frappe.msgprint({
				title: 'Deploy Created',
				indicator: 'green',
				message: __(
					`{0} been created (or found) from current Deploy Candidate`,
					[`<a href="/app/deploy/${data}">Deploy</a>`],
				),
			});
		} else if (method === 'deploy' && !data) {
			frappe.msgprint({ title: 'Deploy could not be created' });
		}

		frm.refresh();
	};
}

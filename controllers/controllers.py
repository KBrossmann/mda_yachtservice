# -*- coding: utf-8 -*-
import base64
import requests
from odoo import http, _
from odoo.http import request


# controller to call the yacht request data entry form
class ServiceRequest(http.Controller):
    @http.route("/service_request", auth="public", type="http", website=True)
    def service_request(self, **post):
        return request.render("mda_yachtservice.create_request", {})

    # controller to post the data into the model yacht_repair and call the thank_you page
    @http.route("/submit", type="http", auth="public", website=True)
    def create_yacht_job(self, **post):
        # reCAPTCHA verification
        recaptcha_response = post.get("g-recaptcha-response")
        secret_key = "6LeSlVApAAAAAM5e6eLIGHsPgK3hVawlFknrt4Mc"  # secret key works only with localhost! Change for different domain
        recaptcha_request_data = {"secret": secret_key, "response": recaptcha_response}
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        response = requests.post(verify_url, data=recaptcha_request_data)
        result = response.json()

        if not result.get("success"):
            # Handle failure: show an error message or redirect
            return request.render("mda_yachtservice.recaptcha_failure", {})
        print(result)
        name = post.get("name")
        email = post.get("email")
        phone = post.get("phone")
        partner = (
            request.env["res.partner"]
            .sudo()
            .create({"name": name, "email": email, "phone": phone})
        )

        yacht_name = post.get("yacht_name")
        description = post.get("description")
        parts_requested = post.get("parts_requested")
        eta = post.get("eta")
        arc = post.get("arc")
        arc_number = post.get("arc_number")

        yacht_service = (
            request.env["yacht.service.client"]
            .sudo()
            .create(
                {
                    "customer": partner.id,
                    "yacht_name": yacht_name,
                    "description": description,
                    "parts_requested": parts_requested,
                    "eta": eta,
                    "arc": arc,
                    "arc_number": arc_number,
                }
            )
        )

        # Handle attachments
        attachment_records = []
        for attachment_data in request.httprequest.files.getlist("attachment"):
            attachment = (
                request.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": attachment_data.filename,
                        "datas": base64.b64encode(attachment_data.read()),
                        "res_model": "yacht.service.client",
                        "res_id": yacht_service.id,
                    }
                )
            )
            attachment_records.append(attachment.id)

        # Update the yacht service record with the attachment IDs
        yacht_service.write({"attachment_field": [(6, 0, attachment_records)]})

        # Construct the group message
        attachment_names = "\n".join(
            request.env["ir.attachment"]
            .sudo()
            .browse(attachment_records)
            .mapped("name")
        )
        group_msg = _(
            "A client has sent %s attachment(s) with this service request ticket. "
            "The names of the attachments are: "
        ) % (len(attachment_records))
        for attachment_id in attachment_records:
            attachment = request.env["ir.attachment"].sudo().browse(attachment_id)
            group_msg += "\n" + attachment.name

        group_msg += (
            "\n"
            + ". You can download attachment(s) from the attachments option on the form here."
        )

        # Post the group message
        yacht_service.sudo().message_post(body=group_msg, message_type="comment")

        # Sending the email using the template
        template_id = request.env.ref(
            "mda_yachtservice.yacht_service_request_confirmation_template"
        )
        if template_id:
            template = template_id.sudo().with_context(
                partner=partner, yacht_service=yacht_service
            )
            template.send_mail(yacht_service.id, force_send=True)

        vals = {
            "partner": partner,
            "yacht_service_record": yacht_service,
            "ref": yacht_service.ref,
        }
        return request.render("mda_yachtservice.request_thanks", vals)

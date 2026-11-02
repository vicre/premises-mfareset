FIDO2_METHOD_TYPE = "#microsoft.graph.fido2AuthenticationMethod"


def prepare_auth_methods(methods, *, include_fido2=False):
    pretty = []

    for method in methods:
        odata_type = method.get("@odata.type", "")
        label = "Unknown method"
        details = ""
        can_delete = False

        if odata_type.endswith("passwordAuthenticationMethod"):
            label = "Password"
            created = method.get("createdDateTime")
            if created:
                details = f"Created: {created}"

        elif odata_type.endswith("phoneAuthenticationMethod"):
            label = "Phone"
            can_delete = True
            phone_type = method.get("phoneType", "")
            phone_number = method.get("phoneNumber", "")
            details = f"{phone_type}: {phone_number}"

        elif odata_type.endswith("microsoftAuthenticatorAuthenticationMethod"):
            label = "Microsoft Authenticator"
            can_delete = True
            display_name = method.get("displayName", "")
            device_tag = method.get("deviceTag", "")
            details = f"{display_name} ({device_tag})"


        elif odata_type.endswith("softwareOathAuthenticationMethod"):
            label = "Software OATH token"
            can_delete = True

        elif odata_type == FIDO2_METHOD_TYPE:
            label = "Passkey / FIDO2 security key"
            can_delete = include_fido2
            display_name = method.get("displayName") or "Unnamed passkey"
            model = method.get("model") or ""
            details = f"{display_name} ({model})" if model else display_name

        elif odata_type.endswith("windowsHelloForBusinessAuthenticationMethod"):
            label = "Windows Hello for Business"
            display_name = method.get("displayName") or "Unnamed device"
            created = method.get("createdDateTime", "")
            details = f"{display_name} (created {created})"

        else:
            details = str(method)

        # only add (show) the method if it can be deleted
        if (can_delete):
            pretty.append(
                {
                    "label": label,
                    "details": details,
                    "id": method.get("id", ""),
                    "type": odata_type,
                    "can_delete": can_delete,
                }
            )
        

    return pretty

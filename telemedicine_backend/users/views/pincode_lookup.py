import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class PincodeLookupAPIView(APIView):
    """Proxy India Post PIN data (api.postalpincode.in) for authenticated users."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        pin = (request.query_params.get("pincode") or "").strip()
        if not pin.isdigit() or len(pin) != 6:
            return Response({"error": "Enter a valid 6-digit PIN code."}, status=400)

        url = f"https://api.postalpincode.in/pincode/{pin}"
        try:
            req = Request(url, headers={"User-Agent": "IRME-Telemedicine/1.0 (Django)"})
            with urlopen(req, timeout=12) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            logger.warning("Pincode lookup failed for %s: %s", pin, exc)
            return Response(
                {"error": "Unable to look up this PIN right now. Enter state and district manually."},
                status=502,
            )

        # api.postalpincode.in returns either [{...}] or {...}
        if isinstance(raw, list):
            payload = raw[0] if raw and isinstance(raw[0], dict) else {}
        elif isinstance(raw, dict):
            payload = raw
        else:
            logger.warning("Unexpected pincode JSON shape for %s: %s", pin, type(raw).__name__)
            return Response(
                {"error": "Unexpected response from PIN directory. Enter state and district manually."},
                status=502,
            )

        if payload.get("Status") != "Success":
            return Response({"error": "No data found for this PIN code."}, status=404)

        offices = payload.get("PostOffice") or []
        if not offices:
            return Response({"error": "No data found for this PIN code."}, status=404)

        first = offices[0]
        if not isinstance(first, dict):
            return Response({"error": "Unexpected PIN directory format."}, status=502)
        return Response(
            {
                "pincode": pin,
                "state": (first.get("State") or "").strip(),
                "district": (first.get("District") or "").strip(),
                "division": (first.get("Division") or "").strip(),
                "post_offices": [
                    {"name": (o.get("Name") or "").strip(), "branch_type": (o.get("BranchType") or "").strip()}
                    for o in offices[:15]
                ],
            },
            status=200,
        )

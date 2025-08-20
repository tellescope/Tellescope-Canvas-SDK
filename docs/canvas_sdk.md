# Loading Secrets

Every protocol that interacts with the Tellescope API must first load secrets. If secrets are not defined, the protocol should return early. Here's an example illustrating how secrets are loaded:
```python
from canvas_sdk.protocols import BaseProtocol
from canvas_sdk.effects import Effect

class Protocol(BaseProtocol):
    def compute(self) -> list[Effect]:
        tellescope_api_key = self.secrets["TELLESCOPE_API_KEY"]
        tellescope_api_url = self.secrets["TELLESCOPE_API_URL"]
```

If testing Tellescope API utilities locally, you can pull these values from the local .env as follows:
```python
import os

tellescope_api_key = os.getenv("TELLESCOPE_API_KEY")
tellescope_api_url = os.getenv("TELLESCOPE_API_URL")

if not tellescope_api_key or not tellescope_api_url:
  raise EnvironmentError("Missing Tellescope API credentials in environment variables.")
```
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

from llm_client import llm
history = []


def ask(user_text):
    history.append({"role": "user", "content": user_text})
    response = llm.complete(
        task="reason",
        max_output_tokens=300,
        system="You are a concise telecom support assistant.",
        messages=history,
    )
    reply = response.text
    history.append({"role": "assistant", "content": reply})
    print("Input tokens:", response.usage.input_tokens)
    return reply


print(ask("My broadband keeps dropping."))
print(ask("It started on Monday."))
print(ask("What did I say started on Monday?"))


"""output was-
Input tokens: 33
Sorry about that. Let's narrow it down.

**Quick checks:**
1. **Restart the router:** Unplug it for 30 seconds, then plug it back in.
2. **Check the cables:** Make sure the phone/fiber/coax line and power cables are firmly seated and undamaged.
3. **Check the router lights:** Note whether any are red, orange, or blinking unusually.
4. **Test wired vs. Wi-Fi:** Connect a device by Ethernet. If the wired connection is stable, the problem is Wi-Fi, not the line.
5. **Rule out interference:** Move the router away from microwaves, cordless phones, and thick walls.

**To help further, tell me:**
- What type of connection do you have (fiber, cable
Input tokens: 294
Thanks, that's useful. A sudden start usually points to something that changed around then.

**Check:**
- **Outage or maintenance:** Look at your provider's status page or app for issues in your area.
- **Changes on Monday:** New equipment, moved furniture or router, a power surge or storm, or a firmwareupdate.
- **Cable damage:** Look for pinched, chewed, or loosened lines, especially outside or where the line enters your home.

**Tell me:**
1. Connection type (fiber, cable, DSL, or wireless)?
2. Do the drops happen at set times or randomly, and how long do they last?
3. Does it aff
Input tokens: 518
You said your broadband dropping started on Monday. That was your reply after you first told me the connection keeps dropping.

To narrow it down, can you tell me:
1. Your connection type (fiber, cable, DSL, or wireless)?
2. Whether the drops happen at set times or randomly, and how long they last?
3. Whether it affects all devices or just some?

"""

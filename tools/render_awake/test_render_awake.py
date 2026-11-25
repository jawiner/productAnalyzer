"""Offline tests for render_awake's decisions (a fake Awake; nothing on the PC changes).

    python -I tools/render_awake/test_render_awake.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_awake import RENDER_RE, AwakeState, Keeper  # noqa: E402


class FakeIO:
    def __init__(self, running=True):
        self.running, self.state, self.self_held, self.writes, self.fail = running, AwakeState(0, 0, 0), False, [], False

    def awake_running(self):
        return self.running

    def read_awake(self):
        return self.state

    def write_awake(self, mode, minutes):
        if self.fail:
            return False
        self.writes.append(mode)
        self.state = AwakeState(mode, 0, minutes if mode else self.state.minutes)
        return True

    def hold_self(self, on):
        self.self_held = on


R = ["reelkit render (pid 1)"]


class KeeperTest(unittest.TestCase):
    def setUp(self):
        self.io = FakeIO()
        self.k = Keeper(self.io, grace_s=180, renew_s=300, minutes=14)

    def test_render_turns_awake_on_renews_and_lets_go_after_grace(self):
        self.assertEqual(self.k.tick(0, R), "awake")
        self.assertEqual((self.io.state.mode, self.io.state.minutes), (2, 14))
        self.k.tick(100, R)
        self.assertEqual(self.io.writes, [2])            # not renewed before 5 min
        self.k.tick(320, R)
        self.assertEqual(self.io.writes, [2, 2])         # renewed
        self.assertEqual(self.k.tick(400, []), "awake")  # render ended: still on during the grace
        self.assertEqual(self.k.tick(600, []), "idle")   # 200 s after the last render
        self.assertEqual(self.io.state.mode, 0)

    def test_idle_never_touches_awake(self):
        self.k.tick(0, [])
        self.assertEqual(self.io.writes, [])

    def test_own_session_from_tray_is_left_alone(self):
        self.io.state = AwakeState(2, 0, 30)
        self.assertIn("your own", self.k.tick(0, R))
        self.k.tick(1000, [])
        self.assertEqual(self.io.writes, [])
        self.assertEqual(self.io.state.minutes, 30)

    def test_own_indefinite_session_survives_the_render_end(self):
        self.k.tick(0, R)
        self.io.state = AwakeState(1, 0, 14)              # owner picks "keep awake indefinitely" mid-render
        self.assertIn("your own", self.k.tick(60, R))
        self.k.tick(1000, [])
        self.assertEqual(self.io.state.mode, 1)

    def test_switched_off_during_render_stays_off_until_render_ends(self):
        self.k.tick(0, R)
        self.io.state = AwakeState(0, 0, 14)              # owner turns Awake off
        self.assertIn("switched off", self.k.tick(60, R))
        self.assertIn("switched off", self.k.tick(400, R))
        self.assertEqual(self.io.writes, [2])
        self.k.tick(1000, [])                             # render over, grace over
        self.assertEqual(self.k.tick(1100, R), "awake")   # the next render is covered again

    def test_timer_ran_out_while_asleep_restarts(self):
        self.k.tick(0, R)
        self.io.state = AwakeState(0, 0, 14)              # 14-min timer ran out (script suspended)
        self.assertEqual(self.k.tick(14 * 60 + 5, R), "awake")
        self.assertEqual(self.io.writes, [2, 2])

    def test_leftover_timer_from_a_crash_is_cleared_when_idle(self):
        self.io.state = AwakeState(2, 0, 14)
        self.k.tick(0, [])
        self.assertEqual(self.io.state.mode, 0)

    def test_no_powertoys_holds_itself_and_lets_go(self):
        self.io.running = False
        self.assertIn("itself", self.k.tick(0, R))
        self.assertTrue(self.io.self_held)
        self.k.tick(500, [])
        self.assertFalse(self.io.self_held)

    def test_awake_coming_back_takes_over_from_self_hold(self):
        self.io.running = False
        self.k.tick(0, R)
        self.io.running = True
        self.assertEqual(self.k.tick(20, R), "awake")
        self.assertFalse(self.io.self_held)

    def test_failed_write_falls_back_to_self_hold(self):
        self.io.fail = True
        self.assertIn("itself", self.k.tick(0, R))
        self.assertTrue(self.io.self_held)

    def test_low_battery_lets_go(self):
        self.k.tick(0, R)
        self.assertIn("battery", self.k.tick(20, R, low_battery=True))
        self.assertEqual(self.io.state.mode, 0)


class MatchTest(unittest.TestCase):
    def find(self, cmd):
        m = RENDER_RE.search(cmd.replace('"', " ").lower())
        return f"{m.group(1)} {m.group(2)}" if m else None

    def test_real_command_lines(self):
        self.assertEqual(self.find(r'"C:\Program Files\nodejs\node.exe" '
                                   r'"C:\Users\x\AppData\Roaming\npm\node_modules\reelkit-cli\bin\reelkit.mjs" render --no-share'),
                         "reelkit render")
        self.assertEqual(self.find(r'node C:\x\node_modules\reelkit-cli\bin\reelkit.mjs export --all'), "reelkit export")
        self.assertEqual(self.find(r'node "C:\p\node_modules\@remotion\cli\remotion-cli.js" render Main out.mp4'),
                         "remotion render")
        self.assertEqual(self.find(r'node C:\x\npx-cli.js hyperframes render'), "hyperframes render")

    def test_not_renders(self):
        self.assertIsNone(self.find(r'node C:\x\reelkit-cli\bin\reelkit.mjs preview --project C:\render'))
        self.assertIsNone(self.find(r'node C:\x\reelkit-cli\bin\reelkit.mjs check'))
        self.assertIsNone(self.find(r'node C:\x\remotion-cli.js studio'))
        self.assertIsNone(self.find(r'node server.js --render-mode fast'))


if __name__ == "__main__":
    unittest.main(verbosity=1)

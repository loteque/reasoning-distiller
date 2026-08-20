#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("ril_cli_g6", ROOT/"runtime"/"ril_cli.py"); cli=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(cli)

class G6CliTests(unittest.TestCase):
    def parse(self,*args): return cli.parser().parse_args(list(args))
    def test_depth_defaults_zero_independent_of_json(self):
        self.assertEqual(self.parse("--json","show","workflow:abc").depth,0)
    def test_depth_accepts_standard_scale(self):
        for n in ("0","1","2"): self.assertEqual(self.parse("show","workflow:abc",f"--depth={n}").depth,int(n))
    def test_depth_rejects_outside_scale(self):
        with self.assertRaises(SystemExit): self.parse("show","workflow:abc","--depth=3")
    def test_presentation_modes_are_exclusive(self):
        with self.assertRaises(SystemExit): self.parse("--json","--quiet","show","workflow:abc")
    def test_quiet_higher_depth_is_invalid(self):
        ns=self.parse("--quiet","show","workflow:abc","--depth=1")
        self.assertEqual(cli.execute(ns,Path("/tmp"))["outcome"],"QUIET_DEPTH_CONFLICT")
    def test_generic_show_requires_typed_reference(self):
        with tempfile.TemporaryDirectory() as td:
            ns=self.parse("show","abc")
            r=cli.execute(ns,Path(td)); self.assertEqual(r["status"],"FAIL")
    def test_project_override_wins(self):
        ns=self.parse("--project","/tmp/example","show","workflow:abc")
        r=cli.execute(ns,Path("/")); self.assertEqual(r["project_root"],str(Path("/tmp/example").resolve()))
    def test_workflow_continue_routes_to_shared_orchestration_surface(self):
        ns=self.parse("workflow","continue","workflow:abc","proposal.json")
        self.assertEqual(ns.resource,"workflow"); self.assertEqual(ns.verb,"continue")
    def test_authority_grant_show_has_depth(self):
        ns=self.parse("authority-grant","show","authority-grant:abc","--depth=2")
        self.assertEqual(ns.depth,2)
    def test_approve_is_direct_operator_surface(self):
        ns=self.parse("approve","proposal.json","--operator","operator:alice")
        self.assertEqual(ns.operator,"operator:alice")

if __name__=="__main__": unittest.main()

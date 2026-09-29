"""Offline analytical and Streamlit regression checks. Run: python test_dashboard.py."""
import json
from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
from metrics import filter_profile, neighborhood_metrics, period_change
from charts import build_explorer_map

ROOT = Path(__file__).parent

class Calculations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_parquet(ROOT / "data/apartamentos_itbi_poa.parquet")

    def test_prepared_values_and_missing(self):
        d = self.df
        self.assertEqual(len(d), 116198)
        self.assertEqual(d.ano_construcao.isna().sum(), 23154)
        self.assertLess((d.valor_m2 - d.base_de_calculo / d.area_constr_privativa).abs().max(), .01)
        all_rows = filter_profile(d, (0, float('inf')), (0, float('inf')))
        self.assertEqual(len(all_rows), len(d))
        known = filter_profile(d, (0, float('inf')), (0, float('inf')), (1916, 2025), False)
        self.assertEqual(len(d)-len(known), 23154)

    def test_denominator_and_endpoints(self):
        d = self.df
        f = filter_profile(d, (250000, 500000), (50, 80))
        s = neighborhood_metrics(d, f, (2020, 2025), 100)
        name = "PETRÓPOLIS"
        n = len(f.loc[f.bairro_oficial.eq(name)])
        denominator = len(d.loc[d.bairro_oficial.eq(name)])
        self.assertAlmostEqual(s.loc[name, "compatibilidade"], n / denominator * 100)
        self.assertLess(s.loc[name, "compatibilidade"], 100)
        self.assertTrue(period_change(d, (2025, 2025), 1).isna().all())
        self.assertTrue(period_change(d, (2020, 2025), len(d)).isna().all())
        first = d.loc[d.bairro_oficial.eq(name) & d.ano.eq(2020), "valor_m2"].median()
        last = d.loc[d.bairro_oficial.eq(name) & d.ano.eq(2025), "valor_m2"].median()
        self.assertAlmostEqual(period_change(d, (2020, 2025), 1)[name], (last/first-1)*100)

    def test_all_polygons_and_zero(self):
        d = self.df
        context = d.loc[d.bairro_oficial.isin(["PETRÓPOLIS", "JAR ITU SABARA"])]
        filtered = context.loc[context.bairro_oficial.eq("JAR ITU SABARA")]
        stats = neighborhood_metrics(context, filtered, (2020, 2025), 100)
        self.assertEqual(stats.loc["PETRÓPOLIS", "compatibilidade"], 0)
        boundaries = json.loads((ROOT / "data/bairros_poa.geojson").read_text(encoding="utf-8"))
        for metric in ("valor_m2", "base_de_calculo", "registros", "compatibilidade", "variacao"):
            m = build_explorer_map(stats, boundaries, metric, 100)
            layer = next(c for c in m._children.values() if hasattr(c, "data") and isinstance(c.data, dict) and "features" in c.data)
            self.assertEqual(len(layer.data["features"]), 94)
            self.assertNotIn("JAR ITU SABARA", [f["properties"]["bairro_oficial"] for f in layer.data["features"]])

class Interface(unittest.TestCase):
    def test_component_host(self):
        a = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
        self.assertFalse(a.exception)
        a.session_state["dashboard_state"] = {"years": [2025, 2025], "metric": "variacao"}
        a.run()
        self.assertFalse(a.exception)

    def test_filter_scenarios(self):
        from dashboard_view import build_payload, default_state
        d = pd.read_parquet(ROOT / "data/apartamentos_itbi_poa.parquet")
        boundaries = json.loads((ROOT / "data/bairros_poa.geojson").read_text(encoding="utf-8"))
        state = default_state(d)
        result = build_payload(d, boundaries, state)
        self.assertFalse(result["empty"])
        self.assertEqual(result["focus_count"], 5847)
        for metric in ("base_de_calculo", "registros", "compatibilidade", "variacao"):
            result = build_payload(d, boundaries, {**state, "metric": metric})
            self.assertIn("map_html", result)
        result = build_payload(d, boundaries, {**state, "years": [2025, 2025], "metric": "variacao"})
        self.assertIn("dois anos", result["metric_note"])
        for names in (["JAR ITU SABARA"], ["PETRÓPOLIS", "MENINO DEUS"]):
            result = build_payload(d, boundaries, {**state, "neighborhoods": names, "comparison": names})
            self.assertEqual(result["options"], sorted(names))
        construction = {**state, "construction_active": True, "construction": [1990, 2020], "include_missing": False}
        result = build_payload(d, boundaries, construction)
        self.assertFalse(result["empty"])
        result = build_payload(d, boundaries, {**construction, "value": [250000., 500000.], "area": [50., 80.]})
        self.assertFalse(result["empty"])
        result = build_payload(d, boundaries, {**state, "minimum": 116199})
        self.assertEqual(result["eligible_count"], 0)
        result = build_payload(d, boundaries, {**state, "value": [15000., 15000.], "area": [50., 80.]})
        self.assertTrue(result["empty"])
        self.assertEqual(default_state(d)["years"], [2020, 2025])

if __name__ == "__main__":
    unittest.main(verbosity=2)

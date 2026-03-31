"""
Export OpenAPI Spec to YAML (AUT-363)

Generates OpenAPI spec from FastAPI app and exports to docs/api/research-backtesting.yaml.
FastAPI auto-generates the spec based on route definitions and Pydantic schemas.

Usage:
    python backend/scripts/export_openapi_spec.py
"""
import yaml
from pathlib import Path
from fastapi import FastAPI

# Import the research router
from app.api.v1.research.routes import router


def export_openapi_spec():
    """
    Generate and export OpenAPI spec to YAML.

    Creates a FastAPI app, includes the research router,
    and exports the generated OpenAPI spec to YAML file.
    """
    # Create FastAPI app
    app = FastAPI(
        title="NQHUB Research & Backtesting API",
        description="""
        Research & Backtesting REST API for NQ Futures trading strategies.

        Provides endpoints for:
        - Backtest execution (async via Celery)
        - Results import from Jupyter notebooks
        - Parameter optimization (grid search, walk-forward)
        - Backtest screener with filters
        - Strategy management (register, validate, list)

        **NQ Constants:**
        - tick_size = 0.25
        - tick_value = $5.00
        - point_value = $20.00

        **Apex Account Defaults:**
        - initial_capital = $25,000
        - max_contracts = 4
        - trailing_threshold = $1,500
        """,
        version="2.0.0",
        contact={
            "name": "NQHUB Engineering",
            "email": "engineering@nqhub.io"
        },
        license_info={
            "name": "Proprietary",
        }
    )

    # Include research router
    app.include_router(router)

    # Generate OpenAPI spec
    openapi_spec = app.openapi()

    # Determine output path
    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "docs" / "api" / "research-backtesting.yaml"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export to YAML
    with open(output_path, "w") as f:
        yaml.dump(
            openapi_spec,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=120
        )

    print(f"✅ OpenAPI spec exported to: {output_path}")
    print(f"📊 Endpoints: {len(openapi_spec['paths'])}")
    print(f"📝 Schemas: {len(openapi_spec.get('components', {}).get('schemas', {}))}")

    # Validate spec
    try:
        from openapi_spec_validator import validate_spec
        validate_spec(openapi_spec)
        print("✅ Spec validation passed")
    except ImportError:
        print("⚠️  openapi-spec-validator not installed, skipping validation")
    except Exception as e:
        print(f"❌ Spec validation failed: {e}")
        return False

    return True


if __name__ == "__main__":
    success = export_openapi_spec()
    exit(0 if success else 1)

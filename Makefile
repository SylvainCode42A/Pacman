# Pac-Man - Makefile
#
# Subject III.2: install / run / debug / clean / lint are mandatory,
# lint-strict is optional but recommended.
# `package` covers chapter VII, which warns the package may have to be
# regenerated during the peer review.

PYTHON     := python3
CONFIG     := config/config.json
MYPY_FLAGS := --warn-return-any --warn-unused-ignores --ignore-missing-imports \
              --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-strict package

install:
	$(PYTHON) -m pip install --upgrade pip
	# pygame and pygame-ce both provide the `pygame` namespace; having both
	# installed loads two SDL2 copies and segfaults on macOS (see
	# management/blocking-points.md), so we always remove both first.
	$(PYTHON) -m pip uninstall -y pygame pygame-ce >/dev/null 2>&1 || true
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install flake8 mypy
	# Assigned A-Maze-ing package (V.4), shipped as a wheel at the root.
	@for w in mazegenerator-*.whl; do \
		[ -e "$$w" ] && $(PYTHON) -m pip install "$$w"; \
	done; true

run:
	$(PYTHON) pac-man.py $(CONFIG)

debug:
	$(PYTHON) -m pdb pac-man.py $(CONFIG)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf .mypy_cache build dist
	rm -f highscores.json

lint:
	flake8 .
	mypy . $(MYPY_FLAGS)

lint-strict:
	flake8 .
	mypy . --strict

package:
	$(PYTHON) -m pip install --upgrade pyinstaller
	pyinstaller --noconfirm pacman.spec

# nbdev template

Use this template to more easily create your nbdev project.

## Stupid things we have to do because Software sucks

Add a kernel spec and change to it inside Jupyter Labs
```
poetry run python -m ipykernel install --user --name proseflow
```

In the `poetry shell`

```
jupyter lab build
```
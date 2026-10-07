# VTK field report, regenerated without MATLAB / ParaView

`make_field_report.py` rebuilds `VTK_Field_Report.xlsx` from `set1.csv` / `set2.csv`:
one cube thumbnail per point, shown next to avg / wavelength / amplitude.

```
python make_field_report.py --set1 set1.csv --set2 set2.csv \
    [--sweep Aums_CM_sweep_2D.csv] [--reference VTK_Field_Report.xlsx] --out .
```

Needs numpy, matplotlib, Pillow, openpyxl.

## How the images are made
`sine.m` writes a volume that only varies along y, `c(y) = avg + amp*sin(2*pi*y/wv)`, with the
last y layer set to `avg`. ParaView only shows the outer surface of that volume, so `cuberender.py`
draws the cube directly from the 1-D profile (side faces follow `c(y)`, top face is the last layer,
colour range auto-scaled to the field, Cool-to-Warm colour map, camera and shading measured from the
original screenshots). No 1280^3 array or ASCII VTK file is ever written.

Because the colour range is auto-scaled, amplitude and average do not change the picture; only the
wavelength does. The stripe count in all 20 original renders is `640 / wavelength`, so both sets are
drawn on a 640-long domain (`sine.m` with `Ny = 1280` would give twice as many for set 2).

## Check against ParaView
`--reference` compares every render to the screenshot in the original workbook:
mean absolute error 1.37 / 255 over the 20 points (worst 2.78, set 2 point 1 with its 8 fine
stripes). Remaining differences are edge anti-aliasing and a slightly different top-face tint.

## Outputs
- `renders/` one PNG per point, named like Aum's `.vtk` files (`point<NN>_wv<λ>nm_amp<amp>pct`, with a `set<N>_` prefix)
- `VTK_Field_Report_regenerated.xlsx` same layout as the original report
- `Aums_CM_sweep_2D_with_renders.xlsx` (only with `--sweep`) Aum's sweep table with the
  `CM render` column filled; not committed because it contains his SIM results

The SIM columns are not computed here: they come from the phase-field simulation, which these
files do not contain.

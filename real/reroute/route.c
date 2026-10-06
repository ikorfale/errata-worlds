/* route.c: priority-flood (epsilon fill) + D8 steepest descent + drainage area + longest true flow path.
   usage: route in.f32 n m dx.f32 dy mode out_prefix
   in.f32: n*m float32 heights, NaN = sea/nodata. dx.f32: n float32, true E-W cell size per row (m). dy: N-S size (m).
   mode 0: D8 slope uses square cells (distance 1 or sqrt2); mode 1: true metric distances.
   out: <prefix>.rec (int32, receiver index, -1 none), .A (float32 km2), .L (float32 km, longest path, true metres). */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdint.h>
typedef struct { float z; int32_t i; } E;
static E *hp; static long hn = 0;
static void push(float z, int32_t i) { long k = hn++; while (k > 0) { long p = (k - 1) / 2; if (hp[p].z <= z) break; hp[k] = hp[p]; k = p; } hp[k].z = z; hp[k].i = i; }
static E pop(void) { E top = hp[0], x = hp[--hn]; long k = 0; for (;;) { long c = 2 * k + 1; if (c >= hn) break; if (c + 1 < hn && hp[c + 1].z < hp[c].z) c++; if (hp[c].z >= x.z) break; hp[k] = hp[c]; k = c; } hp[k] = x; return top; }
int main(int argc, char **argv) {
  if (argc < 8) return 2;
  long n = atol(argv[2]), m = atol(argv[3]), N = n * m; float dy = atof(argv[5]); int mode = atoi(argv[6]);
  float *z = malloc(N * 4), *dx = malloc(n * 4); FILE *f = fopen(argv[1], "rb"); if (fread(z, 4, N, f) != (size_t)N) return 3; fclose(f);
  f = fopen(argv[4], "rb"); if (fread(dx, 4, n, f) != (size_t)n) return 3; fclose(f);
  uint8_t *seen = calloc(N, 1); int32_t *order = malloc(N * 4); long no = 0; hp = malloc(N * sizeof(E));
  int DJ[8] = {0, 1, 1, 1, 0, -1, -1, -1}, DI[8] = {1, 1, 0, -1, -1, -1, 0, 1};
  /* seeds: land cells next to sea/nodata or on the frame */
  for (long j = 0; j < n; j++) for (long i = 0; i < m; i++) { long c = j * m + i; if (isnan(z[c])) { seen[c] = 1; continue; }
    int edge = (j == 0 || i == 0 || j == n - 1 || i == m - 1);
    for (int k = 0; k < 8 && !edge; k++) if (isnan(z[(j + DJ[k]) * m + i + DI[k]])) edge = 1;
    if (edge) { push(z[c], c); seen[c] = 1; } }
  while (hn) { E e = pop(); order[no++] = e.i; long j = e.i / m, i = e.i % m;
    for (int k = 0; k < 8; k++) { long y = j + DJ[k], x = i + DI[k]; if (y < 0 || x < 0 || y >= n || x >= m) continue; long c = y * m + x;
      if (seen[c]) continue; seen[c] = 1; if (z[c] <= e.z) z[c] = nextafterf(e.z, INFINITY); /* lake/flat: smallest rise toward the outlet */ push(z[c], c); } }
  /* D8 steepest descent on the filled surface; outlet cells (seeds with no lower land neighbour) drain to sea: rec -1 */
  int32_t *rec = malloc(N * 4);
  for (long c = 0; c < N; c++) { rec[c] = -1; if (isnan(z[c])) continue; long j = c / m, i = c % m; float best = 0;
    for (int k = 0; k < 8; k++) { long y = j + DJ[k], x = i + DI[k]; if (y < 0 || x < 0 || y >= n || x >= m) continue; long t = y * m + x;
      if (isnan(z[t])) continue; float drop = z[c] - z[t]; if (drop <= 0) continue;
      float d = mode == 0 ? ((DJ[k] && DI[k]) ? 1.41421356f : 1.f) : sqrtf((DJ[k] * dy) * (DJ[k] * dy) + (DI[k] * dx[j]) * (DI[k] * dx[j]));
      if (drop / d > best) { best = drop / d; rec[c] = t; } } }
  float *A = malloc(N * 4), *L = calloc(N, 4);
  for (long c = 0; c < N; c++) A[c] = isnan(z[c]) ? 0 : dx[c / m] * dy / 1e6f;
  for (long q = no - 1; q >= 0; q--) { long c = order[q], t = rec[c]; if (t < 0) continue;
    long dj = t / m - c / m, di = t % m - c % m; float d = sqrtf((dj * dy) * (dj * dy) + (di * dx[c / m]) * (di * dx[c / m])) / 1000.f;
    A[t] += A[c]; if (L[c] + d > L[t]) L[t] = L[c] + d; }
  char p[512];
  sprintf(p, "%s.rec", argv[7]); f = fopen(p, "wb"); fwrite(rec, 4, N, f); fclose(f);
  sprintf(p, "%s.A", argv[7]); f = fopen(p, "wb"); fwrite(A, 4, N, f); fclose(f);
  sprintf(p, "%s.L", argv[7]); f = fopen(p, "wb"); fwrite(L, 4, N, f); fclose(f);
  printf("cells %ld land-ordered %ld\n", N, no); return 0; }

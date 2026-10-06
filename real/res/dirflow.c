/* #133: drainage area A (km2), longest upstream flow length L (km) and "touches the window edge" flag from a
   HydroSHEDS D8 direction grid (1 E, 2 SE, 4 S, 8 SW, 16 W, 32 NW, 64 N, 128 NE; 0 sink, 255 no data).
   usage: dirflow in.u8 n m lat_top cell_deg out_prefix   -> out.A out.L (float32), out.rec (int32, -1 = outlet), out.edge (u8) */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
int main(int c, char **v) {
    if (c < 7) return 1;
    long n = atol(v[2]), m = atol(v[3]), N = n * m; double lat0 = atof(v[4]), cd = atof(v[5]);
    unsigned char *d = malloc(N), *edge = calloc(N, 1); FILE *f = fopen(v[1], "rb"); if (fread(d, 1, N, f) != (size_t)N) return 2; fclose(f);
    int *rec = malloc(N * 4), *deg = calloc(N, 4), *q = malloc(N * 4); float *A = malloc(N * 4), *L = calloc(N, 4);
    const double R = 6371.0, dy = R * cd * M_PI / 180;
    for (long k = 0; k < N; k++) {
        long j = k / m, i = k % m; rec[k] = -1; int di = 0, dj = 0; unsigned char x = d[k];
        double lat = lat0 - (j + 0.5) * cd, dx = dy * cos(lat * M_PI / 180); A[k] = (x == 255) ? 0 : dx * dy;
        if (j == 0 || i == 0 || j == n - 1 || i == m - 1) edge[k] = 1;
        switch (x) { case 1: di = 1; break; case 2: di = 1; dj = 1; break; case 4: dj = 1; break; case 8: di = -1; dj = 1; break;
                     case 16: di = -1; break; case 32: di = -1; dj = -1; break; case 64: dj = -1; break; case 128: di = 1; dj = -1; break; default: continue; }
        long jj = j + dj, ii = i + di; if (jj < 0 || ii < 0 || jj >= n || ii >= m) { edge[k] = 1; continue; }
        long t = jj * m + ii; if (d[t] == 255) continue; rec[k] = t; deg[t]++;
    }
    long h = 0, tl = 0; for (long k = 0; k < N; k++) if (d[k] != 255 && deg[k] == 0) q[tl++] = k;
    while (h < tl) {
        long k = q[h++]; int t = rec[k]; if (t < 0) continue;
        long j = k / m, i = k % m, jj = t / m, ii = t % m; double lat = lat0 - (j + 0.5) * cd, dx = dy * cos(lat * M_PI / 180);
        double s = sqrt(pow((ii - i) * dx, 2) + pow((jj - j) * dy, 2));
        A[t] += A[k]; if (L[k] + s > L[t]) L[t] = L[k] + s; edge[t] |= edge[k];
        if (--deg[t] == 0) q[tl++] = t;
    }
    char p[512]; FILE *o;
    sprintf(p, "%s.A", v[6]); o = fopen(p, "wb"); fwrite(A, 4, N, o); fclose(o);
    sprintf(p, "%s.L", v[6]); o = fopen(p, "wb"); fwrite(L, 4, N, o); fclose(o);
    sprintf(p, "%s.rec", v[6]); o = fopen(p, "wb"); fwrite(rec, 4, N, o); fclose(o);
    sprintf(p, "%s.edge", v[6]); o = fopen(p, "wb"); fwrite(edge, 1, N, o); fclose(o);
    printf("cells %ld processed %ld\n", N, tl); return 0;
}

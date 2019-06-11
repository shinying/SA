#include <Python.h>
#include <math.h>

#define pi 3.1415926

/* Prototype */
double deg2rad(double);
double rad2deg(double);

// dis(km), velo(knot) -> time(hour)
double move_dis_to_time(double dis, double velo) {
    return (dis / 1.852 / velo);
}

// lng1, lat1, lng2, lat2 (degree) -> distance(km)
double count_dis(double lng1, double lat1, double lng2, double lat2) {
    double theta, dist;
    if ((lat1 == lat2) && (lng1 == lng2)) {
        return 0;
    }

    theta = lng1 - lng2;
    dist = sin(deg2rad(lat1)) * sin(deg2rad(lat2)) + 
           cos(deg2rad(lat1)) * cos(deg2rad(lat2)) * cos(deg2rad(theta));
    dist = acos(dist);
    dist = rad2deg(dist);
    dist = dist * 60 * 1.1515;
    dist = dist * 1.609344; // to km
        
    return dist;
}

/* Convert decimal degrees to radians */
double deg2rad(double deg) {
    return deg * pi / 180;
}

/* Convert radians to decimal degrees */
double rad2deg(double rad) {
    return rad * 180 / pi;
}


/* Python interface */

static PyObject* c_move_dis_to_time(PyObject* self, PyObject* args) {
    double dis, velo;
    if (!PyArg_ParseTuple(args, "dd", &dis, &velo))
        return NULL; 
    return Py_BuildValue("d", move_dis_to_time(dis, velo));
}

static PyObject* c_count_dis(PyObject* self, PyObject* args) {
    double lng1, lat1, lng2, lat2;
    if (!PyArg_ParseTuple(args, "dddd", &lng1, &lat1, &lng2, &lat2))
        return NULL; 
    return Py_BuildValue("d", count_dis(lng1, lat1, lng2, lat2));
}

/* Method table */
static PyMethodDef CUtilMethods[] = {
    {"c_move_dis_to_time", c_move_dis_to_time, METH_VARARGS, "Calculate moving time with given distance and speed."},
    {"c_count_dis", c_count_dis, METH_VARARGS, "Measure straight-line distance between two coordinates."},
    {NULL, NULL, 0, NULL}
};

/* Define the information about the module */
static struct PyModuleDef cutilmodule = {
    PyModuleDef_HEAD_INIT,
    "cutil",   // name of module
    "utility functions implemented in C", // module documentation, may be NULL
    -1,
    CUtilMethods
};

/* Initialized function, called when the module is imported */
PyMODINIT_FUNC PyInit_cutil(void) {
    return PyModule_Create(&cutilmodule);
}
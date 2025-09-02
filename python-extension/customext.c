#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *compute(PyObject *self, PyObject *args)
{
    int n;
    PyObject *s; // will hold a Unicode object
    PyObject *m; // must be a dict

    // Parse: int, Unicode (str), dict
    if (!PyArg_ParseTuple(args, "iUO!", &n, &s, &PyDict_Type, &m))
    {
        return NULL; // TypeError is set by PyArg_ParseTuple
    }

    long n_plus = (long)n + 1;

    // s + "ABC"
    PyObject *suffix = PyUnicode_FromString("ABC");
    if (!suffix)
        return NULL;

    PyObject *new_s = PyUnicode_Concat(s, suffix);
    Py_DECREF(suffix);
    if (!new_s)
        return NULL;

    // m["data"] = "-data-"
    PyObject *value = PyUnicode_FromString("-data-");
    if (!value)
    {
        Py_DECREF(new_s);
        return NULL;
    }

    if (PyDict_SetItemString(m, "data", value) < 0)
    {
        Py_DECREF(value);
        Py_DECREF(new_s);
        return NULL;
    }
    Py_DECREF(value);

    // Build return tuple (n_plus, new_s, m)
    PyObject *n_obj = PyLong_FromLong(n_plus);
    if (!n_obj)
    {
        Py_DECREF(new_s);
        return NULL;
    }

    PyObject *result = PyTuple_Pack(3, n_obj, new_s, m);
    Py_DECREF(n_obj);
    Py_DECREF(new_s);
    if (!result)
        return NULL;

    return result;
}

static PyMethodDef CustomExtMethods[] = {
    {"compute", compute, METH_VARARGS,
     "compute(n: int, s: str, m: dict) -> (int, str, dict)\n"
     "Increments n, appends 'ABC' to s, sets m['data'] = '-data-', returns (n, s, m)."},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef customextmodule = {
    PyModuleDef_HEAD_INIT,
    "customext",
    "A minimal example C extension exposing compute().",
    -1,
    CustomExtMethods};

PyMODINIT_FUNC PyInit_customext(void)
{
    return PyModule_Create(&customextmodule);
}

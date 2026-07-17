//#region \0rolldown/runtime.js
var e = Object.create, t = Object.defineProperty, n = Object.getOwnPropertyDescriptor, r = Object.getOwnPropertyNames, i = Object.getPrototypeOf, a = Object.prototype.hasOwnProperty, o = (e, t) => () => (t || (e((t = { exports: {} }).exports, t), e = null), t.exports), s = (e, n) => {
	let r = {};
	for (var i in e) t(r, i, {
		get: e[i],
		enumerable: !0
	});
	return n || t(r, Symbol.toStringTag, { value: "Module" }), r;
}, c = (e, i, o, s) => {
	if (i && typeof i == "object" || typeof i == "function") for (var c = r(i), l = 0, u = c.length, d; l < u; l++) d = c[l], !a.call(e, d) && d !== o && t(e, d, {
		get: ((e) => i[e]).bind(null, d),
		enumerable: !(s = n(i, d)) || s.enumerable
	});
	return e;
}, l = (n, r, a) => (a = n == null ? {} : e(i(n)), c(r || !n || !n.__esModule ? t(a, "default", {
	value: n,
	enumerable: !0
}) : a, n)), u = /* @__PURE__ */ o(((e) => {
	var t = Symbol.for("react.element"), n = Symbol.for("react.portal"), r = Symbol.for("react.fragment"), i = Symbol.for("react.strict_mode"), a = Symbol.for("react.profiler"), o = Symbol.for("react.provider"), s = Symbol.for("react.context"), c = Symbol.for("react.forward_ref"), l = Symbol.for("react.suspense"), u = Symbol.for("react.memo"), d = Symbol.for("react.lazy"), f = Symbol.iterator;
	function p(e) {
		return typeof e != "object" || !e ? null : (e = f && e[f] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var m = {
		isMounted: function() {
			return !1;
		},
		enqueueForceUpdate: function() {},
		enqueueReplaceState: function() {},
		enqueueSetState: function() {}
	}, h = Object.assign, g = {};
	function _(e, t, n) {
		this.props = e, this.context = t, this.refs = g, this.updater = n || m;
	}
	_.prototype.isReactComponent = {}, _.prototype.setState = function(e, t) {
		if (typeof e != "object" && typeof e != "function" && e != null) throw Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
		this.updater.enqueueSetState(this, e, t, "setState");
	}, _.prototype.forceUpdate = function(e) {
		this.updater.enqueueForceUpdate(this, e, "forceUpdate");
	};
	function v() {}
	v.prototype = _.prototype;
	function y(e, t, n) {
		this.props = e, this.context = t, this.refs = g, this.updater = n || m;
	}
	var b = y.prototype = new v();
	b.constructor = y, h(b, _.prototype), b.isPureReactComponent = !0;
	var x = Array.isArray, S = Object.prototype.hasOwnProperty, C = { current: null }, w = {
		key: !0,
		ref: !0,
		__self: !0,
		__source: !0
	};
	function T(e, n, r) {
		var i, a = {}, o = null, s = null;
		if (n != null) for (i in n.ref !== void 0 && (s = n.ref), n.key !== void 0 && (o = "" + n.key), n) S.call(n, i) && !w.hasOwnProperty(i) && (a[i] = n[i]);
		var c = arguments.length - 2;
		if (c === 1) a.children = r;
		else if (1 < c) {
			for (var l = Array(c), u = 0; u < c; u++) l[u] = arguments[u + 2];
			a.children = l;
		}
		if (e && e.defaultProps) for (i in c = e.defaultProps, c) a[i] === void 0 && (a[i] = c[i]);
		return {
			$$typeof: t,
			type: e,
			key: o,
			ref: s,
			props: a,
			_owner: C.current
		};
	}
	function E(e, n) {
		return {
			$$typeof: t,
			type: e.type,
			key: n,
			ref: e.ref,
			props: e.props,
			_owner: e._owner
		};
	}
	function D(e) {
		return typeof e == "object" && !!e && e.$$typeof === t;
	}
	function O(e) {
		var t = {
			"=": "=0",
			":": "=2"
		};
		return "$" + e.replace(/[=:]/g, function(e) {
			return t[e];
		});
	}
	var k = /\/+/g;
	function A(e, t) {
		return typeof e == "object" && e && e.key != null ? O("" + e.key) : t.toString(36);
	}
	function j(e, r, i, a, o) {
		var s = typeof e;
		(s === "undefined" || s === "boolean") && (e = null);
		var c = !1;
		if (e === null) c = !0;
		else switch (s) {
			case "string":
			case "number":
				c = !0;
				break;
			case "object": switch (e.$$typeof) {
				case t:
				case n: c = !0;
			}
		}
		if (c) return c = e, o = o(c), e = a === "" ? "." + A(c, 0) : a, x(o) ? (i = "", e != null && (i = e.replace(k, "$&/") + "/"), j(o, r, i, "", function(e) {
			return e;
		})) : o != null && (D(o) && (o = E(o, i + (!o.key || c && c.key === o.key ? "" : ("" + o.key).replace(k, "$&/") + "/") + e)), r.push(o)), 1;
		if (c = 0, a = a === "" ? "." : a + ":", x(e)) for (var l = 0; l < e.length; l++) {
			s = e[l];
			var u = a + A(s, l);
			c += j(s, r, i, u, o);
		}
		else if (u = p(e), typeof u == "function") for (e = u.call(e), l = 0; !(s = e.next()).done;) s = s.value, u = a + A(s, l++), c += j(s, r, i, u, o);
		else if (s === "object") throw r = String(e), Error("Objects are not valid as a React child (found: " + (r === "[object Object]" ? "object with keys {" + Object.keys(e).join(", ") + "}" : r) + "). If you meant to render a collection of children, use an array instead.");
		return c;
	}
	function M(e, t, n) {
		if (e == null) return e;
		var r = [], i = 0;
		return j(e, r, "", "", function(e) {
			return t.call(n, e, i++);
		}), r;
	}
	function N(e) {
		if (e._status === -1) {
			var t = e._result;
			t = t(), t.then(function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 1, e._result = t);
			}, function(t) {
				(e._status === 0 || e._status === -1) && (e._status = 2, e._result = t);
			}), e._status === -1 && (e._status = 0, e._result = t);
		}
		if (e._status === 1) return e._result.default;
		throw e._result;
	}
	var P = { current: null }, ee = { transition: null }, te = {
		ReactCurrentDispatcher: P,
		ReactCurrentBatchConfig: ee,
		ReactCurrentOwner: C
	};
	function ne() {
		throw Error("act(...) is not supported in production builds of React.");
	}
	e.Children = {
		map: M,
		forEach: function(e, t, n) {
			M(e, function() {
				t.apply(this, arguments);
			}, n);
		},
		count: function(e) {
			var t = 0;
			return M(e, function() {
				t++;
			}), t;
		},
		toArray: function(e) {
			return M(e, function(e) {
				return e;
			}) || [];
		},
		only: function(e) {
			if (!D(e)) throw Error("React.Children.only expected to receive a single React element child.");
			return e;
		}
	}, e.Component = _, e.Fragment = r, e.Profiler = a, e.PureComponent = y, e.StrictMode = i, e.Suspense = l, e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = te, e.act = ne, e.cloneElement = function(e, n, r) {
		if (e == null) throw Error("React.cloneElement(...): The argument must be a React element, but you passed " + e + ".");
		var i = h({}, e.props), a = e.key, o = e.ref, s = e._owner;
		if (n != null) {
			if (n.ref !== void 0 && (o = n.ref, s = C.current), n.key !== void 0 && (a = "" + n.key), e.type && e.type.defaultProps) var c = e.type.defaultProps;
			for (l in n) S.call(n, l) && !w.hasOwnProperty(l) && (i[l] = n[l] === void 0 && c !== void 0 ? c[l] : n[l]);
		}
		var l = arguments.length - 2;
		if (l === 1) i.children = r;
		else if (1 < l) {
			c = Array(l);
			for (var u = 0; u < l; u++) c[u] = arguments[u + 2];
			i.children = c;
		}
		return {
			$$typeof: t,
			type: e.type,
			key: a,
			ref: o,
			props: i,
			_owner: s
		};
	}, e.createContext = function(e) {
		return e = {
			$$typeof: s,
			_currentValue: e,
			_currentValue2: e,
			_threadCount: 0,
			Provider: null,
			Consumer: null,
			_defaultValue: null,
			_globalName: null
		}, e.Provider = {
			$$typeof: o,
			_context: e
		}, e.Consumer = e;
	}, e.createElement = T, e.createFactory = function(e) {
		var t = T.bind(null, e);
		return t.type = e, t;
	}, e.createRef = function() {
		return { current: null };
	}, e.forwardRef = function(e) {
		return {
			$$typeof: c,
			render: e
		};
	}, e.isValidElement = D, e.lazy = function(e) {
		return {
			$$typeof: d,
			_payload: {
				_status: -1,
				_result: e
			},
			_init: N
		};
	}, e.memo = function(e, t) {
		return {
			$$typeof: u,
			type: e,
			compare: t === void 0 ? null : t
		};
	}, e.startTransition = function(e) {
		var t = ee.transition;
		ee.transition = {};
		try {
			e();
		} finally {
			ee.transition = t;
		}
	}, e.unstable_act = ne, e.useCallback = function(e, t) {
		return P.current.useCallback(e, t);
	}, e.useContext = function(e) {
		return P.current.useContext(e);
	}, e.useDebugValue = function() {}, e.useDeferredValue = function(e) {
		return P.current.useDeferredValue(e);
	}, e.useEffect = function(e, t) {
		return P.current.useEffect(e, t);
	}, e.useId = function() {
		return P.current.useId();
	}, e.useImperativeHandle = function(e, t, n) {
		return P.current.useImperativeHandle(e, t, n);
	}, e.useInsertionEffect = function(e, t) {
		return P.current.useInsertionEffect(e, t);
	}, e.useLayoutEffect = function(e, t) {
		return P.current.useLayoutEffect(e, t);
	}, e.useMemo = function(e, t) {
		return P.current.useMemo(e, t);
	}, e.useReducer = function(e, t, n) {
		return P.current.useReducer(e, t, n);
	}, e.useRef = function(e) {
		return P.current.useRef(e);
	}, e.useState = function(e) {
		return P.current.useState(e);
	}, e.useSyncExternalStore = function(e, t, n) {
		return P.current.useSyncExternalStore(e, t, n);
	}, e.useTransition = function() {
		return P.current.useTransition();
	}, e.version = "18.3.1";
})), d = /* @__PURE__ */ o(((e, t) => {
	t.exports = u();
})), f = /* @__PURE__ */ o(((e) => {
	function t(e, t) {
		var n = e.length;
		e.push(t);
		a: for (; 0 < n;) {
			var r = n - 1 >>> 1, a = e[r];
			if (0 < i(a, t)) e[r] = t, e[n] = a, n = r;
			else break a;
		}
	}
	function n(e) {
		return e.length === 0 ? null : e[0];
	}
	function r(e) {
		if (e.length === 0) return null;
		var t = e[0], n = e.pop();
		if (n !== t) {
			e[0] = n;
			a: for (var r = 0, a = e.length, o = a >>> 1; r < o;) {
				var s = 2 * (r + 1) - 1, c = e[s], l = s + 1, u = e[l];
				if (0 > i(c, n)) l < a && 0 > i(u, c) ? (e[r] = u, e[l] = n, r = l) : (e[r] = c, e[s] = n, r = s);
				else if (l < a && 0 > i(u, n)) e[r] = u, e[l] = n, r = l;
				else break a;
			}
		}
		return t;
	}
	function i(e, t) {
		var n = e.sortIndex - t.sortIndex;
		return n === 0 ? e.id - t.id : n;
	}
	if (typeof performance == "object" && typeof performance.now == "function") {
		var a = performance;
		e.unstable_now = function() {
			return a.now();
		};
	} else {
		var o = Date, s = o.now();
		e.unstable_now = function() {
			return o.now() - s;
		};
	}
	var c = [], l = [], u = 1, d = null, f = 3, p = !1, m = !1, h = !1, g = typeof setTimeout == "function" ? setTimeout : null, _ = typeof clearTimeout == "function" ? clearTimeout : null, v = typeof setImmediate < "u" ? setImmediate : null;
	typeof navigator < "u" && navigator.scheduling !== void 0 && navigator.scheduling.isInputPending !== void 0 && navigator.scheduling.isInputPending.bind(navigator.scheduling);
	function y(e) {
		for (var i = n(l); i !== null;) {
			if (i.callback === null) r(l);
			else if (i.startTime <= e) r(l), i.sortIndex = i.expirationTime, t(c, i);
			else break;
			i = n(l);
		}
	}
	function b(e) {
		if (h = !1, y(e), !m) if (n(c) !== null) m = !0, M(x);
		else {
			var t = n(l);
			t !== null && N(b, t.startTime - e);
		}
	}
	function x(t, i) {
		m = !1, h && (h = !1, _(w), w = -1), p = !0;
		var a = f;
		try {
			for (y(i), d = n(c); d !== null && (!(d.expirationTime > i) || t && !D());) {
				var o = d.callback;
				if (typeof o == "function") {
					d.callback = null, f = d.priorityLevel;
					var s = o(d.expirationTime <= i);
					i = e.unstable_now(), typeof s == "function" ? d.callback = s : d === n(c) && r(c), y(i);
				} else r(c);
				d = n(c);
			}
			if (d !== null) var u = !0;
			else {
				var g = n(l);
				g !== null && N(b, g.startTime - i), u = !1;
			}
			return u;
		} finally {
			d = null, f = a, p = !1;
		}
	}
	var S = !1, C = null, w = -1, T = 5, E = -1;
	function D() {
		return !(e.unstable_now() - E < T);
	}
	function O() {
		if (C !== null) {
			var t = e.unstable_now();
			E = t;
			var n = !0;
			try {
				n = C(!0, t);
			} finally {
				n ? k() : (S = !1, C = null);
			}
		} else S = !1;
	}
	var k;
	if (typeof v == "function") k = function() {
		v(O);
	};
	else if (typeof MessageChannel < "u") {
		var A = new MessageChannel(), j = A.port2;
		A.port1.onmessage = O, k = function() {
			j.postMessage(null);
		};
	} else k = function() {
		g(O, 0);
	};
	function M(e) {
		C = e, S || (S = !0, k());
	}
	function N(t, n) {
		w = g(function() {
			t(e.unstable_now());
		}, n);
	}
	e.unstable_IdlePriority = 5, e.unstable_ImmediatePriority = 1, e.unstable_LowPriority = 4, e.unstable_NormalPriority = 3, e.unstable_Profiling = null, e.unstable_UserBlockingPriority = 2, e.unstable_cancelCallback = function(e) {
		e.callback = null;
	}, e.unstable_continueExecution = function() {
		m || p || (m = !0, M(x));
	}, e.unstable_forceFrameRate = function(e) {
		0 > e || 125 < e ? console.error("forceFrameRate takes a positive int between 0 and 125, forcing frame rates higher than 125 fps is not supported") : T = 0 < e ? Math.floor(1e3 / e) : 5;
	}, e.unstable_getCurrentPriorityLevel = function() {
		return f;
	}, e.unstable_getFirstCallbackNode = function() {
		return n(c);
	}, e.unstable_next = function(e) {
		switch (f) {
			case 1:
			case 2:
			case 3:
				var t = 3;
				break;
			default: t = f;
		}
		var n = f;
		f = t;
		try {
			return e();
		} finally {
			f = n;
		}
	}, e.unstable_pauseExecution = function() {}, e.unstable_requestPaint = function() {}, e.unstable_runWithPriority = function(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 3:
			case 4:
			case 5: break;
			default: e = 3;
		}
		var n = f;
		f = e;
		try {
			return t();
		} finally {
			f = n;
		}
	}, e.unstable_scheduleCallback = function(r, i, a) {
		var o = e.unstable_now();
		switch (typeof a == "object" && a ? (a = a.delay, a = typeof a == "number" && 0 < a ? o + a : o) : a = o, r) {
			case 1:
				var s = -1;
				break;
			case 2:
				s = 250;
				break;
			case 5:
				s = 1073741823;
				break;
			case 4:
				s = 1e4;
				break;
			default: s = 5e3;
		}
		return s = a + s, r = {
			id: u++,
			callback: i,
			priorityLevel: r,
			startTime: a,
			expirationTime: s,
			sortIndex: -1
		}, a > o ? (r.sortIndex = a, t(l, r), n(c) === null && r === n(l) && (h ? (_(w), w = -1) : h = !0, N(b, a - o))) : (r.sortIndex = s, t(c, r), m || p || (m = !0, M(x))), r;
	}, e.unstable_shouldYield = D, e.unstable_wrapCallback = function(e) {
		var t = f;
		return function() {
			var n = f;
			f = t;
			try {
				return e.apply(this, arguments);
			} finally {
				f = n;
			}
		};
	};
})), p = /* @__PURE__ */ o(((e, t) => {
	t.exports = f();
})), m = /* @__PURE__ */ o(((e) => {
	var t = d(), n = p();
	function r(e) {
		for (var t = "https://reactjs.org/docs/error-decoder.html?invariant=" + e, n = 1; n < arguments.length; n++) t += "&args[]=" + encodeURIComponent(arguments[n]);
		return "Minified React error #" + e + "; visit " + t + " for the full message or use the non-minified dev environment for full errors and additional helpful warnings.";
	}
	var i = /* @__PURE__ */ new Set(), a = {};
	function o(e, t) {
		s(e, t), s(e + "Capture", t);
	}
	function s(e, t) {
		for (a[e] = t, e = 0; e < t.length; e++) i.add(t[e]);
	}
	var c = !(typeof window > "u" || window.document === void 0 || window.document.createElement === void 0), l = Object.prototype.hasOwnProperty, u = /^[:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD][:A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*$/, f = {}, m = {};
	function h(e) {
		return l.call(m, e) ? !0 : l.call(f, e) ? !1 : u.test(e) ? m[e] = !0 : (f[e] = !0, !1);
	}
	function g(e, t, n, r) {
		if (n !== null && n.type === 0) return !1;
		switch (typeof t) {
			case "function":
			case "symbol": return !0;
			case "boolean": return r ? !1 : n === null ? (e = e.toLowerCase().slice(0, 5), e !== "data-" && e !== "aria-") : !n.acceptsBooleans;
			default: return !1;
		}
	}
	function _(e, t, n, r) {
		if (t == null || g(e, t, n, r)) return !0;
		if (r) return !1;
		if (n !== null) switch (n.type) {
			case 3: return !t;
			case 4: return !1 === t;
			case 5: return isNaN(t);
			case 6: return isNaN(t) || 1 > t;
		}
		return !1;
	}
	function v(e, t, n, r, i, a, o) {
		this.acceptsBooleans = t === 2 || t === 3 || t === 4, this.attributeName = r, this.attributeNamespace = i, this.mustUseProperty = n, this.propertyName = e, this.type = t, this.sanitizeURL = a, this.removeEmptyString = o;
	}
	var y = {};
	"children dangerouslySetInnerHTML defaultValue defaultChecked innerHTML suppressContentEditableWarning suppressHydrationWarning style".split(" ").forEach(function(e) {
		y[e] = new v(e, 0, !1, e, null, !1, !1);
	}), [
		["acceptCharset", "accept-charset"],
		["className", "class"],
		["htmlFor", "for"],
		["httpEquiv", "http-equiv"]
	].forEach(function(e) {
		var t = e[0];
		y[t] = new v(t, 1, !1, e[1], null, !1, !1);
	}), [
		"contentEditable",
		"draggable",
		"spellCheck",
		"value"
	].forEach(function(e) {
		y[e] = new v(e, 2, !1, e.toLowerCase(), null, !1, !1);
	}), [
		"autoReverse",
		"externalResourcesRequired",
		"focusable",
		"preserveAlpha"
	].forEach(function(e) {
		y[e] = new v(e, 2, !1, e, null, !1, !1);
	}), "allowFullScreen async autoFocus autoPlay controls default defer disabled disablePictureInPicture disableRemotePlayback formNoValidate hidden loop noModule noValidate open playsInline readOnly required reversed scoped seamless itemScope".split(" ").forEach(function(e) {
		y[e] = new v(e, 3, !1, e.toLowerCase(), null, !1, !1);
	}), [
		"checked",
		"multiple",
		"muted",
		"selected"
	].forEach(function(e) {
		y[e] = new v(e, 3, !0, e, null, !1, !1);
	}), ["capture", "download"].forEach(function(e) {
		y[e] = new v(e, 4, !1, e, null, !1, !1);
	}), [
		"cols",
		"rows",
		"size",
		"span"
	].forEach(function(e) {
		y[e] = new v(e, 6, !1, e, null, !1, !1);
	}), ["rowSpan", "start"].forEach(function(e) {
		y[e] = new v(e, 5, !1, e.toLowerCase(), null, !1, !1);
	});
	var b = /[\-:]([a-z])/g;
	function x(e) {
		return e[1].toUpperCase();
	}
	"accent-height alignment-baseline arabic-form baseline-shift cap-height clip-path clip-rule color-interpolation color-interpolation-filters color-profile color-rendering dominant-baseline enable-background fill-opacity fill-rule flood-color flood-opacity font-family font-size font-size-adjust font-stretch font-style font-variant font-weight glyph-name glyph-orientation-horizontal glyph-orientation-vertical horiz-adv-x horiz-origin-x image-rendering letter-spacing lighting-color marker-end marker-mid marker-start overline-position overline-thickness paint-order panose-1 pointer-events rendering-intent shape-rendering stop-color stop-opacity strikethrough-position strikethrough-thickness stroke-dasharray stroke-dashoffset stroke-linecap stroke-linejoin stroke-miterlimit stroke-opacity stroke-width text-anchor text-decoration text-rendering underline-position underline-thickness unicode-bidi unicode-range units-per-em v-alphabetic v-hanging v-ideographic v-mathematical vector-effect vert-adv-y vert-origin-x vert-origin-y word-spacing writing-mode xmlns:xlink x-height".split(" ").forEach(function(e) {
		var t = e.replace(b, x);
		y[t] = new v(t, 1, !1, e, null, !1, !1);
	}), "xlink:actuate xlink:arcrole xlink:role xlink:show xlink:title xlink:type".split(" ").forEach(function(e) {
		var t = e.replace(b, x);
		y[t] = new v(t, 1, !1, e, "http://www.w3.org/1999/xlink", !1, !1);
	}), [
		"xml:base",
		"xml:lang",
		"xml:space"
	].forEach(function(e) {
		var t = e.replace(b, x);
		y[t] = new v(t, 1, !1, e, "http://www.w3.org/XML/1998/namespace", !1, !1);
	}), ["tabIndex", "crossOrigin"].forEach(function(e) {
		y[e] = new v(e, 1, !1, e.toLowerCase(), null, !1, !1);
	}), y.xlinkHref = new v("xlinkHref", 1, !1, "xlink:href", "http://www.w3.org/1999/xlink", !0, !1), [
		"src",
		"href",
		"action",
		"formAction"
	].forEach(function(e) {
		y[e] = new v(e, 1, !1, e.toLowerCase(), null, !0, !0);
	});
	function S(e, t, n, r) {
		var i = y.hasOwnProperty(t) ? y[t] : null;
		(i === null ? r || !(2 < t.length) || t[0] !== "o" && t[0] !== "O" || t[1] !== "n" && t[1] !== "N" : i.type !== 0) && (_(t, n, i, r) && (n = null), r || i === null ? h(t) && (n === null ? e.removeAttribute(t) : e.setAttribute(t, "" + n)) : i.mustUseProperty ? e[i.propertyName] = n === null ? i.type !== 3 && "" : n : (t = i.attributeName, r = i.attributeNamespace, n === null ? e.removeAttribute(t) : (i = i.type, n = i === 3 || i === 4 && !0 === n ? "" : "" + n, r ? e.setAttributeNS(r, t, n) : e.setAttribute(t, n))));
	}
	var C = t.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED, w = Symbol.for("react.element"), T = Symbol.for("react.portal"), E = Symbol.for("react.fragment"), D = Symbol.for("react.strict_mode"), O = Symbol.for("react.profiler"), k = Symbol.for("react.provider"), A = Symbol.for("react.context"), j = Symbol.for("react.forward_ref"), M = Symbol.for("react.suspense"), N = Symbol.for("react.suspense_list"), P = Symbol.for("react.memo"), ee = Symbol.for("react.lazy"), te = Symbol.for("react.offscreen"), ne = Symbol.iterator;
	function re(e) {
		return typeof e != "object" || !e ? null : (e = ne && e[ne] || e["@@iterator"], typeof e == "function" ? e : null);
	}
	var F = Object.assign, ie;
	function ae(e) {
		if (ie === void 0) try {
			throw Error();
		} catch (e) {
			var t = e.stack.trim().match(/\n( *(at )?)/);
			ie = t && t[1] || "";
		}
		return "\n" + ie + e;
	}
	var oe = !1;
	function se(e, t) {
		if (!e || oe) return "";
		oe = !0;
		var n = Error.prepareStackTrace;
		Error.prepareStackTrace = void 0;
		try {
			if (t) if (t = function() {
				throw Error();
			}, Object.defineProperty(t.prototype, "props", { set: function() {
				throw Error();
			} }), typeof Reflect == "object" && Reflect.construct) {
				try {
					Reflect.construct(t, []);
				} catch (e) {
					var r = e;
				}
				Reflect.construct(e, [], t);
			} else {
				try {
					t.call();
				} catch (e) {
					r = e;
				}
				e.call(t.prototype);
			}
			else {
				try {
					throw Error();
				} catch (e) {
					r = e;
				}
				e();
			}
		} catch (t) {
			if (t && r && typeof t.stack == "string") {
				for (var i = t.stack.split("\n"), a = r.stack.split("\n"), o = i.length - 1, s = a.length - 1; 1 <= o && 0 <= s && i[o] !== a[s];) s--;
				for (; 1 <= o && 0 <= s; o--, s--) if (i[o] !== a[s]) {
					if (o !== 1 || s !== 1) do
						if (o--, s--, 0 > s || i[o] !== a[s]) {
							var c = "\n" + i[o].replace(" at new ", " at ");
							return e.displayName && c.includes("<anonymous>") && (c = c.replace("<anonymous>", e.displayName)), c;
						}
					while (1 <= o && 0 <= s);
					break;
				}
			}
		} finally {
			oe = !1, Error.prepareStackTrace = n;
		}
		return (e = e ? e.displayName || e.name : "") ? ae(e) : "";
	}
	function ce(e) {
		switch (e.tag) {
			case 5: return ae(e.type);
			case 16: return ae("Lazy");
			case 13: return ae("Suspense");
			case 19: return ae("SuspenseList");
			case 0:
			case 2:
			case 15: return e = se(e.type, !1), e;
			case 11: return e = se(e.type.render, !1), e;
			case 1: return e = se(e.type, !0), e;
			default: return "";
		}
	}
	function le(e) {
		if (e == null) return null;
		if (typeof e == "function") return e.displayName || e.name || null;
		if (typeof e == "string") return e;
		switch (e) {
			case E: return "Fragment";
			case T: return "Portal";
			case O: return "Profiler";
			case D: return "StrictMode";
			case M: return "Suspense";
			case N: return "SuspenseList";
		}
		if (typeof e == "object") switch (e.$$typeof) {
			case A: return (e.displayName || "Context") + ".Consumer";
			case k: return (e._context.displayName || "Context") + ".Provider";
			case j:
				var t = e.render;
				return e = e.displayName, e || (e = t.displayName || t.name || "", e = e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
			case P: return t = e.displayName || null, t === null ? le(e.type) || "Memo" : t;
			case ee:
				t = e._payload, e = e._init;
				try {
					return le(e(t));
				} catch (e) {}
		}
		return null;
	}
	function ue(e) {
		var t = e.type;
		switch (e.tag) {
			case 24: return "Cache";
			case 9: return (t.displayName || "Context") + ".Consumer";
			case 10: return (t._context.displayName || "Context") + ".Provider";
			case 18: return "DehydratedFragment";
			case 11: return e = t.render, e = e.displayName || e.name || "", t.displayName || (e === "" ? "ForwardRef" : "ForwardRef(" + e + ")");
			case 7: return "Fragment";
			case 5: return t;
			case 4: return "Portal";
			case 3: return "Root";
			case 6: return "Text";
			case 16: return le(t);
			case 8: return t === D ? "StrictMode" : "Mode";
			case 22: return "Offscreen";
			case 12: return "Profiler";
			case 21: return "Scope";
			case 13: return "Suspense";
			case 19: return "SuspenseList";
			case 25: return "TracingMarker";
			case 1:
			case 0:
			case 17:
			case 2:
			case 14:
			case 15:
				if (typeof t == "function") return t.displayName || t.name || null;
				if (typeof t == "string") return t;
		}
		return null;
	}
	function de(e) {
		switch (typeof e) {
			case "boolean":
			case "number":
			case "string":
			case "undefined": return e;
			case "object": return e;
			default: return "";
		}
	}
	function fe(e) {
		var t = e.type;
		return (e = e.nodeName) && e.toLowerCase() === "input" && (t === "checkbox" || t === "radio");
	}
	function pe(e) {
		var t = fe(e) ? "checked" : "value", n = Object.getOwnPropertyDescriptor(e.constructor.prototype, t), r = "" + e[t];
		if (!e.hasOwnProperty(t) && n !== void 0 && typeof n.get == "function" && typeof n.set == "function") {
			var i = n.get, a = n.set;
			return Object.defineProperty(e, t, {
				configurable: !0,
				get: function() {
					return i.call(this);
				},
				set: function(e) {
					r = "" + e, a.call(this, e);
				}
			}), Object.defineProperty(e, t, { enumerable: n.enumerable }), {
				getValue: function() {
					return r;
				},
				setValue: function(e) {
					r = "" + e;
				},
				stopTracking: function() {
					e._valueTracker = null, delete e[t];
				}
			};
		}
	}
	function me(e) {
		e._valueTracker || (e._valueTracker = pe(e));
	}
	function he(e) {
		if (!e) return !1;
		var t = e._valueTracker;
		if (!t) return !0;
		var n = t.getValue(), r = "";
		return e && (r = fe(e) ? e.checked ? "true" : "false" : e.value), e = r, e === n ? !1 : (t.setValue(e), !0);
	}
	function ge(e) {
		if (e = e || (typeof document < "u" ? document : void 0), e === void 0) return null;
		try {
			return e.activeElement || e.body;
		} catch (t) {
			return e.body;
		}
	}
	function _e(e, t) {
		var n = t.checked;
		return F({}, t, {
			defaultChecked: void 0,
			defaultValue: void 0,
			value: void 0,
			checked: n == null ? e._wrapperState.initialChecked : n
		});
	}
	function ve(e, t) {
		var n = t.defaultValue == null ? "" : t.defaultValue, r = t.checked == null ? t.defaultChecked : t.checked;
		n = de(t.value == null ? n : t.value), e._wrapperState = {
			initialChecked: r,
			initialValue: n,
			controlled: t.type === "checkbox" || t.type === "radio" ? t.checked != null : t.value != null
		};
	}
	function ye(e, t) {
		t = t.checked, t != null && S(e, "checked", t, !1);
	}
	function be(e, t) {
		ye(e, t);
		var n = de(t.value), r = t.type;
		if (n != null) r === "number" ? (n === 0 && e.value === "" || e.value != n) && (e.value = "" + n) : e.value !== "" + n && (e.value = "" + n);
		else if (r === "submit" || r === "reset") {
			e.removeAttribute("value");
			return;
		}
		t.hasOwnProperty("value") ? Se(e, t.type, n) : t.hasOwnProperty("defaultValue") && Se(e, t.type, de(t.defaultValue)), t.checked == null && t.defaultChecked != null && (e.defaultChecked = !!t.defaultChecked);
	}
	function xe(e, t, n) {
		if (t.hasOwnProperty("value") || t.hasOwnProperty("defaultValue")) {
			var r = t.type;
			if (!(r !== "submit" && r !== "reset" || t.value !== void 0 && t.value !== null)) return;
			t = "" + e._wrapperState.initialValue, n || t === e.value || (e.value = t), e.defaultValue = t;
		}
		n = e.name, n !== "" && (e.name = ""), e.defaultChecked = !!e._wrapperState.initialChecked, n !== "" && (e.name = n);
	}
	function Se(e, t, n) {
		(t !== "number" || ge(e.ownerDocument) !== e) && (n == null ? e.defaultValue = "" + e._wrapperState.initialValue : e.defaultValue !== "" + n && (e.defaultValue = "" + n));
	}
	var Ce = Array.isArray;
	function we(e, t, n, r) {
		if (e = e.options, t) {
			t = {};
			for (var i = 0; i < n.length; i++) t["$" + n[i]] = !0;
			for (n = 0; n < e.length; n++) i = t.hasOwnProperty("$" + e[n].value), e[n].selected !== i && (e[n].selected = i), i && r && (e[n].defaultSelected = !0);
		} else {
			for (n = "" + de(n), t = null, i = 0; i < e.length; i++) {
				if (e[i].value === n) {
					e[i].selected = !0, r && (e[i].defaultSelected = !0);
					return;
				}
				t !== null || e[i].disabled || (t = e[i]);
			}
			t !== null && (t.selected = !0);
		}
	}
	function Te(e, t) {
		if (t.dangerouslySetInnerHTML != null) throw Error(r(91));
		return F({}, t, {
			value: void 0,
			defaultValue: void 0,
			children: "" + e._wrapperState.initialValue
		});
	}
	function Ee(e, t) {
		var n = t.value;
		if (n == null) {
			if (n = t.children, t = t.defaultValue, n != null) {
				if (t != null) throw Error(r(92));
				if (Ce(n)) {
					if (1 < n.length) throw Error(r(93));
					n = n[0];
				}
				t = n;
			}
			t == null && (t = ""), n = t;
		}
		e._wrapperState = { initialValue: de(n) };
	}
	function De(e, t) {
		var n = de(t.value), r = de(t.defaultValue);
		n != null && (n = "" + n, n !== e.value && (e.value = n), t.defaultValue == null && e.defaultValue !== n && (e.defaultValue = n)), r != null && (e.defaultValue = "" + r);
	}
	function Oe(e) {
		var t = e.textContent;
		t === e._wrapperState.initialValue && t !== "" && t !== null && (e.value = t);
	}
	function ke(e) {
		switch (e) {
			case "svg": return "http://www.w3.org/2000/svg";
			case "math": return "http://www.w3.org/1998/Math/MathML";
			default: return "http://www.w3.org/1999/xhtml";
		}
	}
	function Ae(e, t) {
		return e == null || e === "http://www.w3.org/1999/xhtml" ? ke(t) : e === "http://www.w3.org/2000/svg" && t === "foreignObject" ? "http://www.w3.org/1999/xhtml" : e;
	}
	var je, Me = function(e) {
		return typeof MSApp < "u" && MSApp.execUnsafeLocalFunction ? function(t, n, r, i) {
			MSApp.execUnsafeLocalFunction(function() {
				return e(t, n, r, i);
			});
		} : e;
	}(function(e, t) {
		if (e.namespaceURI !== "http://www.w3.org/2000/svg" || "innerHTML" in e) e.innerHTML = t;
		else {
			for (je = je || document.createElement("div"), je.innerHTML = "<svg>" + t.valueOf().toString() + "</svg>", t = je.firstChild; e.firstChild;) e.removeChild(e.firstChild);
			for (; t.firstChild;) e.appendChild(t.firstChild);
		}
	});
	function Ne(e, t) {
		if (t) {
			var n = e.firstChild;
			if (n && n === e.lastChild && n.nodeType === 3) {
				n.nodeValue = t;
				return;
			}
		}
		e.textContent = t;
	}
	var Pe = {
		animationIterationCount: !0,
		aspectRatio: !0,
		borderImageOutset: !0,
		borderImageSlice: !0,
		borderImageWidth: !0,
		boxFlex: !0,
		boxFlexGroup: !0,
		boxOrdinalGroup: !0,
		columnCount: !0,
		columns: !0,
		flex: !0,
		flexGrow: !0,
		flexPositive: !0,
		flexShrink: !0,
		flexNegative: !0,
		flexOrder: !0,
		gridArea: !0,
		gridRow: !0,
		gridRowEnd: !0,
		gridRowSpan: !0,
		gridRowStart: !0,
		gridColumn: !0,
		gridColumnEnd: !0,
		gridColumnSpan: !0,
		gridColumnStart: !0,
		fontWeight: !0,
		lineClamp: !0,
		lineHeight: !0,
		opacity: !0,
		order: !0,
		orphans: !0,
		tabSize: !0,
		widows: !0,
		zIndex: !0,
		zoom: !0,
		fillOpacity: !0,
		floodOpacity: !0,
		stopOpacity: !0,
		strokeDasharray: !0,
		strokeDashoffset: !0,
		strokeMiterlimit: !0,
		strokeOpacity: !0,
		strokeWidth: !0
	}, Fe = [
		"Webkit",
		"ms",
		"Moz",
		"O"
	];
	Object.keys(Pe).forEach(function(e) {
		Fe.forEach(function(t) {
			t = t + e.charAt(0).toUpperCase() + e.substring(1), Pe[t] = Pe[e];
		});
	});
	function Ie(e, t, n) {
		return t == null || typeof t == "boolean" || t === "" ? "" : n || typeof t != "number" || t === 0 || Pe.hasOwnProperty(e) && Pe[e] ? ("" + t).trim() : t + "px";
	}
	function Le(e, t) {
		for (var n in e = e.style, t) if (t.hasOwnProperty(n)) {
			var r = n.indexOf("--") === 0, i = Ie(n, t[n], r);
			n === "float" && (n = "cssFloat"), r ? e.setProperty(n, i) : e[n] = i;
		}
	}
	var Re = F({ menuitem: !0 }, {
		area: !0,
		base: !0,
		br: !0,
		col: !0,
		embed: !0,
		hr: !0,
		img: !0,
		input: !0,
		keygen: !0,
		link: !0,
		meta: !0,
		param: !0,
		source: !0,
		track: !0,
		wbr: !0
	});
	function ze(e, t) {
		if (t) {
			if (Re[e] && (t.children != null || t.dangerouslySetInnerHTML != null)) throw Error(r(137, e));
			if (t.dangerouslySetInnerHTML != null) {
				if (t.children != null) throw Error(r(60));
				if (typeof t.dangerouslySetInnerHTML != "object" || !("__html" in t.dangerouslySetInnerHTML)) throw Error(r(61));
			}
			if (t.style != null && typeof t.style != "object") throw Error(r(62));
		}
	}
	function Be(e, t) {
		if (e.indexOf("-") === -1) return typeof t.is == "string";
		switch (e) {
			case "annotation-xml":
			case "color-profile":
			case "font-face":
			case "font-face-src":
			case "font-face-uri":
			case "font-face-format":
			case "font-face-name":
			case "missing-glyph": return !1;
			default: return !0;
		}
	}
	var Ve = null;
	function He(e) {
		return e = e.target || e.srcElement || window, e.correspondingUseElement && (e = e.correspondingUseElement), e.nodeType === 3 ? e.parentNode : e;
	}
	var Ue = null, We = null, Ge = null;
	function Ke(e) {
		if (e = Hi(e)) {
			if (typeof Ue != "function") throw Error(r(280));
			var t = e.stateNode;
			t && (t = Wi(t), Ue(e.stateNode, e.type, t));
		}
	}
	function qe(e) {
		We ? Ge ? Ge.push(e) : Ge = [e] : We = e;
	}
	function Je() {
		if (We) {
			var e = We, t = Ge;
			if (Ge = We = null, Ke(e), t) for (e = 0; e < t.length; e++) Ke(t[e]);
		}
	}
	function Ye(e, t) {
		return e(t);
	}
	function Xe() {}
	var Ze = !1;
	function Qe(e, t, n) {
		if (Ze) return e(t, n);
		Ze = !0;
		try {
			return Ye(e, t, n);
		} finally {
			Ze = !1, (We !== null || Ge !== null) && (Xe(), Je());
		}
	}
	function $e(e, t) {
		var n = e.stateNode;
		if (n === null) return null;
		var i = Wi(n);
		if (i === null) return null;
		n = i[t];
		a: switch (t) {
			case "onClick":
			case "onClickCapture":
			case "onDoubleClick":
			case "onDoubleClickCapture":
			case "onMouseDown":
			case "onMouseDownCapture":
			case "onMouseMove":
			case "onMouseMoveCapture":
			case "onMouseUp":
			case "onMouseUpCapture":
			case "onMouseEnter":
				(i = !i.disabled) || (e = e.type, i = !(e === "button" || e === "input" || e === "select" || e === "textarea")), e = !i;
				break a;
			default: e = !1;
		}
		if (e) return null;
		if (n && typeof n != "function") throw Error(r(231, t, typeof n));
		return n;
	}
	var et = !1;
	if (c) try {
		var tt = {};
		Object.defineProperty(tt, "passive", { get: function() {
			et = !0;
		} }), window.addEventListener("test", tt, tt), window.removeEventListener("test", tt, tt);
	} catch (e) {
		et = !1;
	}
	function nt(e, t, n, r, i, a, o, s, c) {
		var l = Array.prototype.slice.call(arguments, 3);
		try {
			t.apply(n, l);
		} catch (e) {
			this.onError(e);
		}
	}
	var rt = !1, it = null, at = !1, ot = null, st = { onError: function(e) {
		rt = !0, it = e;
	} };
	function ct(e, t, n, r, i, a, o, s, c) {
		rt = !1, it = null, nt.apply(st, arguments);
	}
	function lt(e, t, n, i, a, o, s, c, l) {
		if (ct.apply(this, arguments), rt) {
			if (rt) {
				var u = it;
				rt = !1, it = null;
			} else throw Error(r(198));
			at || (at = !0, ot = u);
		}
	}
	function ut(e) {
		var t = e, n = e;
		if (e.alternate) for (; t.return;) t = t.return;
		else {
			e = t;
			do
				t = e, t.flags & 4098 && (n = t.return), e = t.return;
			while (e);
		}
		return t.tag === 3 ? n : null;
	}
	function dt(e) {
		if (e.tag === 13) {
			var t = e.memoizedState;
			if (t === null && (e = e.alternate, e !== null && (t = e.memoizedState)), t !== null) return t.dehydrated;
		}
		return null;
	}
	function ft(e) {
		if (ut(e) !== e) throw Error(r(188));
	}
	function pt(e) {
		var t = e.alternate;
		if (!t) {
			if (t = ut(e), t === null) throw Error(r(188));
			return t === e ? e : null;
		}
		for (var n = e, i = t;;) {
			var a = n.return;
			if (a === null) break;
			var o = a.alternate;
			if (o === null) {
				if (i = a.return, i !== null) {
					n = i;
					continue;
				}
				break;
			}
			if (a.child === o.child) {
				for (o = a.child; o;) {
					if (o === n) return ft(a), e;
					if (o === i) return ft(a), t;
					o = o.sibling;
				}
				throw Error(r(188));
			}
			if (n.return !== i.return) n = a, i = o;
			else {
				for (var s = !1, c = a.child; c;) {
					if (c === n) {
						s = !0, n = a, i = o;
						break;
					}
					if (c === i) {
						s = !0, i = a, n = o;
						break;
					}
					c = c.sibling;
				}
				if (!s) {
					for (c = o.child; c;) {
						if (c === n) {
							s = !0, n = o, i = a;
							break;
						}
						if (c === i) {
							s = !0, i = o, n = a;
							break;
						}
						c = c.sibling;
					}
					if (!s) throw Error(r(189));
				}
			}
			if (n.alternate !== i) throw Error(r(190));
		}
		if (n.tag !== 3) throw Error(r(188));
		return n.stateNode.current === n ? e : t;
	}
	function mt(e) {
		return e = pt(e), e === null ? null : ht(e);
	}
	function ht(e) {
		if (e.tag === 5 || e.tag === 6) return e;
		for (e = e.child; e !== null;) {
			var t = ht(e);
			if (t !== null) return t;
			e = e.sibling;
		}
		return null;
	}
	var gt = n.unstable_scheduleCallback, _t = n.unstable_cancelCallback, vt = n.unstable_shouldYield, yt = n.unstable_requestPaint, bt = n.unstable_now, xt = n.unstable_getCurrentPriorityLevel, St = n.unstable_ImmediatePriority, Ct = n.unstable_UserBlockingPriority, wt = n.unstable_NormalPriority, Tt = n.unstable_LowPriority, Et = n.unstable_IdlePriority, Dt = null, Ot = null;
	function kt(e) {
		if (Ot && typeof Ot.onCommitFiberRoot == "function") try {
			Ot.onCommitFiberRoot(Dt, e, void 0, (e.current.flags & 128) == 128);
		} catch (e) {}
	}
	var I = Math.clz32 ? Math.clz32 : Mt, At = Math.log, jt = Math.LN2;
	function Mt(e) {
		return e >>>= 0, e === 0 ? 32 : 31 - (At(e) / jt | 0) | 0;
	}
	var Nt = 64, Pt = 4194304;
	function Ft(e) {
		switch (e & -e) {
			case 1: return 1;
			case 2: return 2;
			case 4: return 4;
			case 8: return 8;
			case 16: return 16;
			case 32: return 32;
			case 64:
			case 128:
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return e & 4194240;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432:
			case 67108864: return e & 130023424;
			case 134217728: return 134217728;
			case 268435456: return 268435456;
			case 536870912: return 536870912;
			case 1073741824: return 1073741824;
			default: return e;
		}
	}
	function It(e, t) {
		var n = e.pendingLanes;
		if (n === 0) return 0;
		var r = 0, i = e.suspendedLanes, a = e.pingedLanes, o = n & 268435455;
		if (o !== 0) {
			var s = o & ~i;
			s === 0 ? (a &= o, a !== 0 && (r = Ft(a))) : r = Ft(s);
		} else o = n & ~i, o === 0 ? a !== 0 && (r = Ft(a)) : r = Ft(o);
		if (r === 0) return 0;
		if (t !== 0 && t !== r && (t & i) === 0 && (i = r & -r, a = t & -t, i >= a || i === 16 && a & 4194240)) return t;
		if (r & 4 && (r |= n & 16), t = e.entangledLanes, t !== 0) for (e = e.entanglements, t &= r; 0 < t;) n = 31 - I(t), i = 1 << n, r |= e[n], t &= ~i;
		return r;
	}
	function Lt(e, t) {
		switch (e) {
			case 1:
			case 2:
			case 4: return t + 250;
			case 8:
			case 16:
			case 32:
			case 64:
			case 128:
			case 256:
			case 512:
			case 1024:
			case 2048:
			case 4096:
			case 8192:
			case 16384:
			case 32768:
			case 65536:
			case 131072:
			case 262144:
			case 524288:
			case 1048576:
			case 2097152: return t + 5e3;
			case 4194304:
			case 8388608:
			case 16777216:
			case 33554432:
			case 67108864: return -1;
			case 134217728:
			case 268435456:
			case 536870912:
			case 1073741824: return -1;
			default: return -1;
		}
	}
	function Rt(e, t) {
		for (var n = e.suspendedLanes, r = e.pingedLanes, i = e.expirationTimes, a = e.pendingLanes; 0 < a;) {
			var o = 31 - I(a), s = 1 << o, c = i[o];
			c === -1 ? ((s & n) === 0 || (s & r) !== 0) && (i[o] = Lt(s, t)) : c <= t && (e.expiredLanes |= s), a &= ~s;
		}
	}
	function zt(e) {
		return e = e.pendingLanes & -1073741825, e === 0 ? e & 1073741824 ? 1073741824 : 0 : e;
	}
	function Bt() {
		var e = Nt;
		return Nt <<= 1, !(Nt & 4194240) && (Nt = 64), e;
	}
	function Vt(e) {
		for (var t = [], n = 0; 31 > n; n++) t.push(e);
		return t;
	}
	function Ht(e, t, n) {
		e.pendingLanes |= t, t !== 536870912 && (e.suspendedLanes = 0, e.pingedLanes = 0), e = e.eventTimes, t = 31 - I(t), e[t] = n;
	}
	function Ut(e, t) {
		var n = e.pendingLanes & ~t;
		e.pendingLanes = t, e.suspendedLanes = 0, e.pingedLanes = 0, e.expiredLanes &= t, e.mutableReadLanes &= t, e.entangledLanes &= t, t = e.entanglements;
		var r = e.eventTimes;
		for (e = e.expirationTimes; 0 < n;) {
			var i = 31 - I(n), a = 1 << i;
			t[i] = 0, r[i] = -1, e[i] = -1, n &= ~a;
		}
	}
	function Wt(e, t) {
		var n = e.entangledLanes |= t;
		for (e = e.entanglements; n;) {
			var r = 31 - I(n), i = 1 << r;
			i & t | e[r] & t && (e[r] |= t), n &= ~i;
		}
	}
	var L = 0;
	function Gt(e) {
		return e &= -e, 1 < e ? 4 < e ? e & 268435455 ? 16 : 536870912 : 4 : 1;
	}
	var Kt, qt, Jt, Yt, Xt, Zt = !1, Qt = [], $t = null, en = null, tn = null, nn = /* @__PURE__ */ new Map(), rn = /* @__PURE__ */ new Map(), an = [], on = "mousedown mouseup touchcancel touchend touchstart auxclick dblclick pointercancel pointerdown pointerup dragend dragstart drop compositionend compositionstart keydown keypress keyup input textInput copy cut paste click change contextmenu reset submit".split(" ");
	function sn(e, t) {
		switch (e) {
			case "focusin":
			case "focusout":
				$t = null;
				break;
			case "dragenter":
			case "dragleave":
				en = null;
				break;
			case "mouseover":
			case "mouseout":
				tn = null;
				break;
			case "pointerover":
			case "pointerout":
				nn.delete(t.pointerId);
				break;
			case "gotpointercapture":
			case "lostpointercapture": rn.delete(t.pointerId);
		}
	}
	function cn(e, t, n, r, i, a) {
		return e === null || e.nativeEvent !== a ? (e = {
			blockedOn: t,
			domEventName: n,
			eventSystemFlags: r,
			nativeEvent: a,
			targetContainers: [i]
		}, t !== null && (t = Hi(t), t !== null && qt(t)), e) : (e.eventSystemFlags |= r, t = e.targetContainers, i !== null && t.indexOf(i) === -1 && t.push(i), e);
	}
	function ln(e, t, n, r, i) {
		switch (t) {
			case "focusin": return $t = cn($t, e, t, n, r, i), !0;
			case "dragenter": return en = cn(en, e, t, n, r, i), !0;
			case "mouseover": return tn = cn(tn, e, t, n, r, i), !0;
			case "pointerover":
				var a = i.pointerId;
				return nn.set(a, cn(nn.get(a) || null, e, t, n, r, i)), !0;
			case "gotpointercapture": return a = i.pointerId, rn.set(a, cn(rn.get(a) || null, e, t, n, r, i)), !0;
		}
		return !1;
	}
	function un(e) {
		var t = Vi(e.target);
		if (t !== null) {
			var n = ut(t);
			if (n !== null) {
				if (t = n.tag, t === 13) {
					if (t = dt(n), t !== null) {
						e.blockedOn = t, Xt(e.priority, function() {
							Jt(n);
						});
						return;
					}
				} else if (t === 3 && n.stateNode.current.memoizedState.isDehydrated) {
					e.blockedOn = n.tag === 3 ? n.stateNode.containerInfo : null;
					return;
				}
			}
		}
		e.blockedOn = null;
	}
	function dn(e) {
		if (e.blockedOn !== null) return !1;
		for (var t = e.targetContainers; 0 < t.length;) {
			var n = Sn(e.domEventName, e.eventSystemFlags, t[0], e.nativeEvent);
			if (n === null) {
				n = e.nativeEvent;
				var r = new n.constructor(n.type, n);
				Ve = r, n.target.dispatchEvent(r), Ve = null;
			} else return t = Hi(n), t !== null && qt(t), e.blockedOn = n, !1;
			t.shift();
		}
		return !0;
	}
	function fn(e, t, n) {
		dn(e) && n.delete(t);
	}
	function pn() {
		Zt = !1, $t !== null && dn($t) && ($t = null), en !== null && dn(en) && (en = null), tn !== null && dn(tn) && (tn = null), nn.forEach(fn), rn.forEach(fn);
	}
	function mn(e, t) {
		e.blockedOn === t && (e.blockedOn = null, Zt || (Zt = !0, n.unstable_scheduleCallback(n.unstable_NormalPriority, pn)));
	}
	function hn(e) {
		function t(t) {
			return mn(t, e);
		}
		if (0 < Qt.length) {
			mn(Qt[0], e);
			for (var n = 1; n < Qt.length; n++) {
				var r = Qt[n];
				r.blockedOn === e && (r.blockedOn = null);
			}
		}
		for ($t !== null && mn($t, e), en !== null && mn(en, e), tn !== null && mn(tn, e), nn.forEach(t), rn.forEach(t), n = 0; n < an.length; n++) r = an[n], r.blockedOn === e && (r.blockedOn = null);
		for (; 0 < an.length && (n = an[0], n.blockedOn === null);) un(n), n.blockedOn === null && an.shift();
	}
	var gn = C.ReactCurrentBatchConfig, _n = !0;
	function vn(e, t, n, r) {
		var i = L, a = gn.transition;
		gn.transition = null;
		try {
			L = 1, bn(e, t, n, r);
		} finally {
			L = i, gn.transition = a;
		}
	}
	function yn(e, t, n, r) {
		var i = L, a = gn.transition;
		gn.transition = null;
		try {
			L = 4, bn(e, t, n, r);
		} finally {
			L = i, gn.transition = a;
		}
	}
	function bn(e, t, n, r) {
		if (_n) {
			var i = Sn(e, t, n, r);
			if (i === null) pi(e, t, r, xn, n), sn(e, r);
			else if (ln(i, e, t, n, r)) r.stopPropagation();
			else if (sn(e, r), t & 4 && -1 < on.indexOf(e)) {
				for (; i !== null;) {
					var a = Hi(i);
					if (a !== null && Kt(a), a = Sn(e, t, n, r), a === null && pi(e, t, r, xn, n), a === i) break;
					i = a;
				}
				i !== null && r.stopPropagation();
			} else pi(e, t, r, null, n);
		}
	}
	var xn = null;
	function Sn(e, t, n, r) {
		if (xn = null, e = He(r), e = Vi(e), e !== null) if (t = ut(e), t === null) e = null;
		else if (n = t.tag, n === 13) {
			if (e = dt(t), e !== null) return e;
			e = null;
		} else if (n === 3) {
			if (t.stateNode.current.memoizedState.isDehydrated) return t.tag === 3 ? t.stateNode.containerInfo : null;
			e = null;
		} else t !== e && (e = null);
		return xn = e, null;
	}
	function Cn(e) {
		switch (e) {
			case "cancel":
			case "click":
			case "close":
			case "contextmenu":
			case "copy":
			case "cut":
			case "auxclick":
			case "dblclick":
			case "dragend":
			case "dragstart":
			case "drop":
			case "focusin":
			case "focusout":
			case "input":
			case "invalid":
			case "keydown":
			case "keypress":
			case "keyup":
			case "mousedown":
			case "mouseup":
			case "paste":
			case "pause":
			case "play":
			case "pointercancel":
			case "pointerdown":
			case "pointerup":
			case "ratechange":
			case "reset":
			case "resize":
			case "seeked":
			case "submit":
			case "touchcancel":
			case "touchend":
			case "touchstart":
			case "volumechange":
			case "change":
			case "selectionchange":
			case "textInput":
			case "compositionstart":
			case "compositionend":
			case "compositionupdate":
			case "beforeblur":
			case "afterblur":
			case "beforeinput":
			case "blur":
			case "fullscreenchange":
			case "focus":
			case "hashchange":
			case "popstate":
			case "select":
			case "selectstart": return 1;
			case "drag":
			case "dragenter":
			case "dragexit":
			case "dragleave":
			case "dragover":
			case "mousemove":
			case "mouseout":
			case "mouseover":
			case "pointermove":
			case "pointerout":
			case "pointerover":
			case "scroll":
			case "toggle":
			case "touchmove":
			case "wheel":
			case "mouseenter":
			case "mouseleave":
			case "pointerenter":
			case "pointerleave": return 4;
			case "message": switch (xt()) {
				case St: return 1;
				case Ct: return 4;
				case wt:
				case Tt: return 16;
				case Et: return 536870912;
				default: return 16;
			}
			default: return 16;
		}
	}
	var wn = null, Tn = null, En = null;
	function Dn() {
		if (En) return En;
		var e, t = Tn, n = t.length, r, i = "value" in wn ? wn.value : wn.textContent, a = i.length;
		for (e = 0; e < n && t[e] === i[e]; e++);
		var o = n - e;
		for (r = 1; r <= o && t[n - r] === i[a - r]; r++);
		return En = i.slice(e, 1 < r ? 1 - r : void 0);
	}
	function On(e) {
		var t = e.keyCode;
		return "charCode" in e ? (e = e.charCode, e === 0 && t === 13 && (e = 13)) : e = t, e === 10 && (e = 13), 32 <= e || e === 13 ? e : 0;
	}
	function kn() {
		return !0;
	}
	function An() {
		return !1;
	}
	function jn(e) {
		function t(t, n, r, i, a) {
			for (var o in this._reactName = t, this._targetInst = r, this.type = n, this.nativeEvent = i, this.target = a, this.currentTarget = null, e) e.hasOwnProperty(o) && (t = e[o], this[o] = t ? t(i) : i[o]);
			return this.isDefaultPrevented = (i.defaultPrevented == null ? !1 === i.returnValue : i.defaultPrevented) ? kn : An, this.isPropagationStopped = An, this;
		}
		return F(t.prototype, {
			preventDefault: function() {
				this.defaultPrevented = !0;
				var e = this.nativeEvent;
				e && (e.preventDefault ? e.preventDefault() : typeof e.returnValue != "unknown" && (e.returnValue = !1), this.isDefaultPrevented = kn);
			},
			stopPropagation: function() {
				var e = this.nativeEvent;
				e && (e.stopPropagation ? e.stopPropagation() : typeof e.cancelBubble != "unknown" && (e.cancelBubble = !0), this.isPropagationStopped = kn);
			},
			persist: function() {},
			isPersistent: kn
		}), t;
	}
	var Mn = {
		eventPhase: 0,
		bubbles: 0,
		cancelable: 0,
		timeStamp: function(e) {
			return e.timeStamp || Date.now();
		},
		defaultPrevented: 0,
		isTrusted: 0
	}, Nn = jn(Mn), Pn = F({}, Mn, {
		view: 0,
		detail: 0
	}), Fn = jn(Pn), In, Ln, Rn, zn = F({}, Pn, {
		screenX: 0,
		screenY: 0,
		clientX: 0,
		clientY: 0,
		pageX: 0,
		pageY: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		getModifierState: Xn,
		button: 0,
		buttons: 0,
		relatedTarget: function(e) {
			return e.relatedTarget === void 0 ? e.fromElement === e.srcElement ? e.toElement : e.fromElement : e.relatedTarget;
		},
		movementX: function(e) {
			return "movementX" in e ? e.movementX : (e !== Rn && (Rn && e.type === "mousemove" ? (In = e.screenX - Rn.screenX, Ln = e.screenY - Rn.screenY) : Ln = In = 0, Rn = e), In);
		},
		movementY: function(e) {
			return "movementY" in e ? e.movementY : Ln;
		}
	}), Bn = jn(zn), Vn = jn(F({}, zn, { dataTransfer: 0 })), Hn = jn(F({}, Pn, { relatedTarget: 0 })), Un = jn(F({}, Mn, {
		animationName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), Wn = jn(F({}, Mn, { clipboardData: function(e) {
		return "clipboardData" in e ? e.clipboardData : window.clipboardData;
	} })), Gn = jn(F({}, Mn, { data: 0 })), Kn = {
		Esc: "Escape",
		Spacebar: " ",
		Left: "ArrowLeft",
		Up: "ArrowUp",
		Right: "ArrowRight",
		Down: "ArrowDown",
		Del: "Delete",
		Win: "OS",
		Menu: "ContextMenu",
		Apps: "ContextMenu",
		Scroll: "ScrollLock",
		MozPrintableKey: "Unidentified"
	}, qn = {
		8: "Backspace",
		9: "Tab",
		12: "Clear",
		13: "Enter",
		16: "Shift",
		17: "Control",
		18: "Alt",
		19: "Pause",
		20: "CapsLock",
		27: "Escape",
		32: " ",
		33: "PageUp",
		34: "PageDown",
		35: "End",
		36: "Home",
		37: "ArrowLeft",
		38: "ArrowUp",
		39: "ArrowRight",
		40: "ArrowDown",
		45: "Insert",
		46: "Delete",
		112: "F1",
		113: "F2",
		114: "F3",
		115: "F4",
		116: "F5",
		117: "F6",
		118: "F7",
		119: "F8",
		120: "F9",
		121: "F10",
		122: "F11",
		123: "F12",
		144: "NumLock",
		145: "ScrollLock",
		224: "Meta"
	}, Jn = {
		Alt: "altKey",
		Control: "ctrlKey",
		Meta: "metaKey",
		Shift: "shiftKey"
	};
	function Yn(e) {
		var t = this.nativeEvent;
		return t.getModifierState ? t.getModifierState(e) : (e = Jn[e]) ? !!t[e] : !1;
	}
	function Xn() {
		return Yn;
	}
	var Zn = jn(F({}, Pn, {
		key: function(e) {
			if (e.key) {
				var t = Kn[e.key] || e.key;
				if (t !== "Unidentified") return t;
			}
			return e.type === "keypress" ? (e = On(e), e === 13 ? "Enter" : String.fromCharCode(e)) : e.type === "keydown" || e.type === "keyup" ? qn[e.keyCode] || "Unidentified" : "";
		},
		code: 0,
		location: 0,
		ctrlKey: 0,
		shiftKey: 0,
		altKey: 0,
		metaKey: 0,
		repeat: 0,
		locale: 0,
		getModifierState: Xn,
		charCode: function(e) {
			return e.type === "keypress" ? On(e) : 0;
		},
		keyCode: function(e) {
			return e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		},
		which: function(e) {
			return e.type === "keypress" ? On(e) : e.type === "keydown" || e.type === "keyup" ? e.keyCode : 0;
		}
	})), Qn = jn(F({}, zn, {
		pointerId: 0,
		width: 0,
		height: 0,
		pressure: 0,
		tangentialPressure: 0,
		tiltX: 0,
		tiltY: 0,
		twist: 0,
		pointerType: 0,
		isPrimary: 0
	})), $n = jn(F({}, Pn, {
		touches: 0,
		targetTouches: 0,
		changedTouches: 0,
		altKey: 0,
		metaKey: 0,
		ctrlKey: 0,
		shiftKey: 0,
		getModifierState: Xn
	})), er = jn(F({}, Mn, {
		propertyName: 0,
		elapsedTime: 0,
		pseudoElement: 0
	})), tr = jn(F({}, zn, {
		deltaX: function(e) {
			return "deltaX" in e ? e.deltaX : "wheelDeltaX" in e ? -e.wheelDeltaX : 0;
		},
		deltaY: function(e) {
			return "deltaY" in e ? e.deltaY : "wheelDeltaY" in e ? -e.wheelDeltaY : "wheelDelta" in e ? -e.wheelDelta : 0;
		},
		deltaZ: 0,
		deltaMode: 0
	})), nr = [
		9,
		13,
		27,
		32
	], rr = c && "CompositionEvent" in window, ir = null;
	c && "documentMode" in document && (ir = document.documentMode);
	var ar = c && "TextEvent" in window && !ir, or = c && (!rr || ir && 8 < ir && 11 >= ir), sr = " ", cr = !1;
	function lr(e, t) {
		switch (e) {
			case "keyup": return nr.indexOf(t.keyCode) !== -1;
			case "keydown": return t.keyCode !== 229;
			case "keypress":
			case "mousedown":
			case "focusout": return !0;
			default: return !1;
		}
	}
	function ur(e) {
		return e = e.detail, typeof e == "object" && "data" in e ? e.data : null;
	}
	var R = !1;
	function dr(e, t) {
		switch (e) {
			case "compositionend": return ur(t);
			case "keypress": return t.which === 32 ? (cr = !0, sr) : null;
			case "textInput": return e = t.data, e === sr && cr ? null : e;
			default: return null;
		}
	}
	function fr(e, t) {
		if (R) return e === "compositionend" || !rr && lr(e, t) ? (e = Dn(), En = Tn = wn = null, R = !1, e) : null;
		switch (e) {
			case "paste": return null;
			case "keypress":
				if (!(t.ctrlKey || t.altKey || t.metaKey) || t.ctrlKey && t.altKey) {
					if (t.char && 1 < t.char.length) return t.char;
					if (t.which) return String.fromCharCode(t.which);
				}
				return null;
			case "compositionend": return or && t.locale !== "ko" ? null : t.data;
			default: return null;
		}
	}
	var pr = {
		color: !0,
		date: !0,
		datetime: !0,
		"datetime-local": !0,
		email: !0,
		month: !0,
		number: !0,
		password: !0,
		range: !0,
		search: !0,
		tel: !0,
		text: !0,
		time: !0,
		url: !0,
		week: !0
	};
	function z(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t === "input" ? !!pr[e.type] : t === "textarea";
	}
	function mr(e, t, n, r) {
		qe(r), t = hi(t, "onChange"), 0 < t.length && (n = new Nn("onChange", "change", null, n, r), e.push({
			event: n,
			listeners: t
		}));
	}
	var hr = null, gr = null;
	function _r(e) {
		si(e, 0);
	}
	function vr(e) {
		if (he(Ui(e))) return e;
	}
	function yr(e, t) {
		if (e === "change") return t;
	}
	var br = !1;
	if (c) {
		var xr;
		if (c) {
			var Sr = "oninput" in document;
			if (!Sr) {
				var Cr = document.createElement("div");
				Cr.setAttribute("oninput", "return;"), Sr = typeof Cr.oninput == "function";
			}
			xr = Sr;
		} else xr = !1;
		br = xr && (!document.documentMode || 9 < document.documentMode);
	}
	function wr() {
		hr && (hr.detachEvent("onpropertychange", Tr), gr = hr = null);
	}
	function Tr(e) {
		if (e.propertyName === "value" && vr(gr)) {
			var t = [];
			mr(t, gr, e, He(e)), Qe(_r, t);
		}
	}
	function Er(e, t, n) {
		e === "focusin" ? (wr(), hr = t, gr = n, hr.attachEvent("onpropertychange", Tr)) : e === "focusout" && wr();
	}
	function Dr(e) {
		if (e === "selectionchange" || e === "keyup" || e === "keydown") return vr(gr);
	}
	function Or(e, t) {
		if (e === "click") return vr(t);
	}
	function kr(e, t) {
		if (e === "input" || e === "change") return vr(t);
	}
	function Ar(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var B = typeof Object.is == "function" ? Object.is : Ar;
	function jr(e, t) {
		if (B(e, t)) return !0;
		if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
		var n = Object.keys(e), r = Object.keys(t);
		if (n.length !== r.length) return !1;
		for (r = 0; r < n.length; r++) {
			var i = n[r];
			if (!l.call(t, i) || !B(e[i], t[i])) return !1;
		}
		return !0;
	}
	function Mr(e) {
		for (; e && e.firstChild;) e = e.firstChild;
		return e;
	}
	function Nr(e, t) {
		var n = Mr(e);
		e = 0;
		for (var r; n;) {
			if (n.nodeType === 3) {
				if (r = e + n.textContent.length, e <= t && r >= t) return {
					node: n,
					offset: t - e
				};
				e = r;
			}
			a: {
				for (; n;) {
					if (n.nextSibling) {
						n = n.nextSibling;
						break a;
					}
					n = n.parentNode;
				}
				n = void 0;
			}
			n = Mr(n);
		}
	}
	function Pr(e, t) {
		return e && t ? e === t ? !0 : e && e.nodeType === 3 ? !1 : t && t.nodeType === 3 ? Pr(e, t.parentNode) : "contains" in e ? e.contains(t) : e.compareDocumentPosition ? !!(e.compareDocumentPosition(t) & 16) : !1 : !1;
	}
	function Fr() {
		for (var e = window, t = ge(); t instanceof e.HTMLIFrameElement;) {
			try {
				var n = typeof t.contentWindow.location.href == "string";
			} catch (e) {
				n = !1;
			}
			if (n) e = t.contentWindow;
			else break;
			t = ge(e.document);
		}
		return t;
	}
	function Ir(e) {
		var t = e && e.nodeName && e.nodeName.toLowerCase();
		return t && (t === "input" && (e.type === "text" || e.type === "search" || e.type === "tel" || e.type === "url" || e.type === "password") || t === "textarea" || e.contentEditable === "true");
	}
	function Lr(e) {
		var t = Fr(), n = e.focusedElem, r = e.selectionRange;
		if (t !== n && n && n.ownerDocument && Pr(n.ownerDocument.documentElement, n)) {
			if (r !== null && Ir(n)) {
				if (t = r.start, e = r.end, e === void 0 && (e = t), "selectionStart" in n) n.selectionStart = t, n.selectionEnd = Math.min(e, n.value.length);
				else if (e = (t = n.ownerDocument || document) && t.defaultView || window, e.getSelection) {
					e = e.getSelection();
					var i = n.textContent.length, a = Math.min(r.start, i);
					r = r.end === void 0 ? a : Math.min(r.end, i), !e.extend && a > r && (i = r, r = a, a = i), i = Nr(n, a);
					var o = Nr(n, r);
					i && o && (e.rangeCount !== 1 || e.anchorNode !== i.node || e.anchorOffset !== i.offset || e.focusNode !== o.node || e.focusOffset !== o.offset) && (t = t.createRange(), t.setStart(i.node, i.offset), e.removeAllRanges(), a > r ? (e.addRange(t), e.extend(o.node, o.offset)) : (t.setEnd(o.node, o.offset), e.addRange(t)));
				}
			}
			for (t = [], e = n; e = e.parentNode;) e.nodeType === 1 && t.push({
				element: e,
				left: e.scrollLeft,
				top: e.scrollTop
			});
			for (typeof n.focus == "function" && n.focus(), n = 0; n < t.length; n++) e = t[n], e.element.scrollLeft = e.left, e.element.scrollTop = e.top;
		}
	}
	var Rr = c && "documentMode" in document && 11 >= document.documentMode, zr = null, Br = null, Vr = null, Hr = !1;
	function Ur(e, t, n) {
		var r = n.window === n ? n.document : n.nodeType === 9 ? n : n.ownerDocument;
		Hr || zr == null || zr !== ge(r) || (r = zr, "selectionStart" in r && Ir(r) ? r = {
			start: r.selectionStart,
			end: r.selectionEnd
		} : (r = (r.ownerDocument && r.ownerDocument.defaultView || window).getSelection(), r = {
			anchorNode: r.anchorNode,
			anchorOffset: r.anchorOffset,
			focusNode: r.focusNode,
			focusOffset: r.focusOffset
		}), Vr && jr(Vr, r) || (Vr = r, r = hi(Br, "onSelect"), 0 < r.length && (t = new Nn("onSelect", "select", null, t, n), e.push({
			event: t,
			listeners: r
		}), t.target = zr)));
	}
	function Wr(e, t) {
		var n = {};
		return n[e.toLowerCase()] = t.toLowerCase(), n["Webkit" + e] = "webkit" + t, n["Moz" + e] = "moz" + t, n;
	}
	var Gr = {
		animationend: Wr("Animation", "AnimationEnd"),
		animationiteration: Wr("Animation", "AnimationIteration"),
		animationstart: Wr("Animation", "AnimationStart"),
		transitionend: Wr("Transition", "TransitionEnd")
	}, Kr = {}, qr = {};
	c && (qr = document.createElement("div").style, "AnimationEvent" in window || (delete Gr.animationend.animation, delete Gr.animationiteration.animation, delete Gr.animationstart.animation), "TransitionEvent" in window || delete Gr.transitionend.transition);
	function Jr(e) {
		if (Kr[e]) return Kr[e];
		if (!Gr[e]) return e;
		var t = Gr[e], n;
		for (n in t) if (t.hasOwnProperty(n) && n in qr) return Kr[e] = t[n];
		return e;
	}
	var Yr = Jr("animationend"), Xr = Jr("animationiteration"), Zr = Jr("animationstart"), Qr = Jr("transitionend"), $r = /* @__PURE__ */ new Map(), ei = "abort auxClick cancel canPlay canPlayThrough click close contextMenu copy cut drag dragEnd dragEnter dragExit dragLeave dragOver dragStart drop durationChange emptied encrypted ended error gotPointerCapture input invalid keyDown keyPress keyUp load loadedData loadedMetadata loadStart lostPointerCapture mouseDown mouseMove mouseOut mouseOver mouseUp paste pause play playing pointerCancel pointerDown pointerMove pointerOut pointerOver pointerUp progress rateChange reset resize seeked seeking stalled submit suspend timeUpdate touchCancel touchEnd touchStart volumeChange scroll toggle touchMove waiting wheel".split(" ");
	function ti(e, t) {
		$r.set(e, t), o(t, [e]);
	}
	for (var ni = 0; ni < ei.length; ni++) {
		var ri = ei[ni];
		ti(ri.toLowerCase(), "on" + (ri[0].toUpperCase() + ri.slice(1)));
	}
	ti(Yr, "onAnimationEnd"), ti(Xr, "onAnimationIteration"), ti(Zr, "onAnimationStart"), ti("dblclick", "onDoubleClick"), ti("focusin", "onFocus"), ti("focusout", "onBlur"), ti(Qr, "onTransitionEnd"), s("onMouseEnter", ["mouseout", "mouseover"]), s("onMouseLeave", ["mouseout", "mouseover"]), s("onPointerEnter", ["pointerout", "pointerover"]), s("onPointerLeave", ["pointerout", "pointerover"]), o("onChange", "change click focusin focusout input keydown keyup selectionchange".split(" ")), o("onSelect", "focusout contextmenu dragend focusin keydown keyup mousedown mouseup selectionchange".split(" ")), o("onBeforeInput", [
		"compositionend",
		"keypress",
		"textInput",
		"paste"
	]), o("onCompositionEnd", "compositionend focusout keydown keypress keyup mousedown".split(" ")), o("onCompositionStart", "compositionstart focusout keydown keypress keyup mousedown".split(" ")), o("onCompositionUpdate", "compositionupdate focusout keydown keypress keyup mousedown".split(" "));
	var ii = "abort canplay canplaythrough durationchange emptied encrypted ended error loadeddata loadedmetadata loadstart pause play playing progress ratechange resize seeked seeking stalled suspend timeupdate volumechange waiting".split(" "), ai = new Set("cancel close invalid load scroll toggle".split(" ").concat(ii));
	function oi(e, t, n) {
		var r = e.type || "unknown-event";
		e.currentTarget = n, lt(r, t, void 0, e), e.currentTarget = null;
	}
	function si(e, t) {
		t = (t & 4) != 0;
		for (var n = 0; n < e.length; n++) {
			var r = e[n], i = r.event;
			r = r.listeners;
			a: {
				var a = void 0;
				if (t) for (var o = r.length - 1; 0 <= o; o--) {
					var s = r[o], c = s.instance, l = s.currentTarget;
					if (s = s.listener, c !== a && i.isPropagationStopped()) break a;
					oi(i, s, l), a = c;
				}
				else for (o = 0; o < r.length; o++) {
					if (s = r[o], c = s.instance, l = s.currentTarget, s = s.listener, c !== a && i.isPropagationStopped()) break a;
					oi(i, s, l), a = c;
				}
			}
		}
		if (at) throw e = ot, at = !1, ot = null, e;
	}
	function ci(e, t) {
		var n = t[Ri];
		n === void 0 && (n = t[Ri] = /* @__PURE__ */ new Set());
		var r = e + "__bubble";
		n.has(r) || (fi(t, e, 2, !1), n.add(r));
	}
	function li(e, t, n) {
		var r = 0;
		t && (r |= 4), fi(n, e, r, t);
	}
	var ui = "_reactListening" + Math.random().toString(36).slice(2);
	function di(e) {
		if (!e[ui]) {
			e[ui] = !0, i.forEach(function(t) {
				t !== "selectionchange" && (ai.has(t) || li(t, !1, e), li(t, !0, e));
			});
			var t = e.nodeType === 9 ? e : e.ownerDocument;
			t === null || t[ui] || (t[ui] = !0, li("selectionchange", !1, t));
		}
	}
	function fi(e, t, n, r) {
		switch (Cn(t)) {
			case 1:
				var i = vn;
				break;
			case 4:
				i = yn;
				break;
			default: i = bn;
		}
		n = i.bind(null, t, n, e), i = void 0, !et || t !== "touchstart" && t !== "touchmove" && t !== "wheel" || (i = !0), r ? i === void 0 ? e.addEventListener(t, n, !0) : e.addEventListener(t, n, {
			capture: !0,
			passive: i
		}) : i === void 0 ? e.addEventListener(t, n, !1) : e.addEventListener(t, n, { passive: i });
	}
	function pi(e, t, n, r, i) {
		var a = r;
		if (!(t & 1) && !(t & 2) && r !== null) a: for (;;) {
			if (r === null) return;
			var o = r.tag;
			if (o === 3 || o === 4) {
				var s = r.stateNode.containerInfo;
				if (s === i || s.nodeType === 8 && s.parentNode === i) break;
				if (o === 4) for (o = r.return; o !== null;) {
					var c = o.tag;
					if ((c === 3 || c === 4) && (c = o.stateNode.containerInfo, c === i || c.nodeType === 8 && c.parentNode === i)) return;
					o = o.return;
				}
				for (; s !== null;) {
					if (o = Vi(s), o === null) return;
					if (c = o.tag, c === 5 || c === 6) {
						r = a = o;
						continue a;
					}
					s = s.parentNode;
				}
			}
			r = r.return;
		}
		Qe(function() {
			var r = a, i = He(n), o = [];
			a: {
				var s = $r.get(e);
				if (s !== void 0) {
					var c = Nn, l = e;
					switch (e) {
						case "keypress": if (On(n) === 0) break a;
						case "keydown":
						case "keyup":
							c = Zn;
							break;
						case "focusin":
							l = "focus", c = Hn;
							break;
						case "focusout":
							l = "blur", c = Hn;
							break;
						case "beforeblur":
						case "afterblur":
							c = Hn;
							break;
						case "click": if (n.button === 2) break a;
						case "auxclick":
						case "dblclick":
						case "mousedown":
						case "mousemove":
						case "mouseup":
						case "mouseout":
						case "mouseover":
						case "contextmenu":
							c = Bn;
							break;
						case "drag":
						case "dragend":
						case "dragenter":
						case "dragexit":
						case "dragleave":
						case "dragover":
						case "dragstart":
						case "drop":
							c = Vn;
							break;
						case "touchcancel":
						case "touchend":
						case "touchmove":
						case "touchstart":
							c = $n;
							break;
						case Yr:
						case Xr:
						case Zr:
							c = Un;
							break;
						case Qr:
							c = er;
							break;
						case "scroll":
							c = Fn;
							break;
						case "wheel":
							c = tr;
							break;
						case "copy":
						case "cut":
						case "paste":
							c = Wn;
							break;
						case "gotpointercapture":
						case "lostpointercapture":
						case "pointercancel":
						case "pointerdown":
						case "pointermove":
						case "pointerout":
						case "pointerover":
						case "pointerup": c = Qn;
					}
					var u = (t & 4) != 0, d = !u && e === "scroll", f = u ? s === null ? null : s + "Capture" : s;
					u = [];
					for (var p = r, m; p !== null;) {
						m = p;
						var h = m.stateNode;
						if (m.tag === 5 && h !== null && (m = h, f !== null && (h = $e(p, f), h != null && u.push(mi(p, h, m)))), d) break;
						p = p.return;
					}
					0 < u.length && (s = new c(s, l, null, n, i), o.push({
						event: s,
						listeners: u
					}));
				}
			}
			if (!(t & 7)) {
				a: {
					if (s = e === "mouseover" || e === "pointerover", c = e === "mouseout" || e === "pointerout", s && n !== Ve && (l = n.relatedTarget || n.fromElement) && (Vi(l) || l[Li])) break a;
					if ((c || s) && (s = i.window === i ? i : (s = i.ownerDocument) ? s.defaultView || s.parentWindow : window, c ? (l = n.relatedTarget || n.toElement, c = r, l = l ? Vi(l) : null, l !== null && (d = ut(l), l !== d || l.tag !== 5 && l.tag !== 6) && (l = null)) : (c = null, l = r), c !== l)) {
						if (u = Bn, h = "onMouseLeave", f = "onMouseEnter", p = "mouse", (e === "pointerout" || e === "pointerover") && (u = Qn, h = "onPointerLeave", f = "onPointerEnter", p = "pointer"), d = c == null ? s : Ui(c), m = l == null ? s : Ui(l), s = new u(h, p + "leave", c, n, i), s.target = d, s.relatedTarget = m, h = null, Vi(i) === r && (u = new u(f, p + "enter", l, n, i), u.target = m, u.relatedTarget = d, h = u), d = h, c && l) b: {
							for (u = c, f = l, p = 0, m = u; m; m = gi(m)) p++;
							for (m = 0, h = f; h; h = gi(h)) m++;
							for (; 0 < p - m;) u = gi(u), p--;
							for (; 0 < m - p;) f = gi(f), m--;
							for (; p--;) {
								if (u === f || f !== null && u === f.alternate) break b;
								u = gi(u), f = gi(f);
							}
							u = null;
						}
						else u = null;
						c !== null && _i(o, s, c, u, !1), l !== null && d !== null && _i(o, d, l, u, !0);
					}
				}
				a: {
					if (s = r ? Ui(r) : window, c = s.nodeName && s.nodeName.toLowerCase(), c === "select" || c === "input" && s.type === "file") var g = yr;
					else if (z(s)) if (br) g = kr;
					else {
						g = Dr;
						var _ = Er;
					}
					else (c = s.nodeName) && c.toLowerCase() === "input" && (s.type === "checkbox" || s.type === "radio") && (g = Or);
					if (g && (g = g(e, r))) {
						mr(o, g, n, i);
						break a;
					}
					_ && _(e, s, r), e === "focusout" && (_ = s._wrapperState) && _.controlled && s.type === "number" && Se(s, "number", s.value);
				}
				switch (_ = r ? Ui(r) : window, e) {
					case "focusin":
						(z(_) || _.contentEditable === "true") && (zr = _, Br = r, Vr = null);
						break;
					case "focusout":
						Vr = Br = zr = null;
						break;
					case "mousedown":
						Hr = !0;
						break;
					case "contextmenu":
					case "mouseup":
					case "dragend":
						Hr = !1, Ur(o, n, i);
						break;
					case "selectionchange": if (Rr) break;
					case "keydown":
					case "keyup": Ur(o, n, i);
				}
				var v;
				if (rr) b: {
					switch (e) {
						case "compositionstart":
							var y = "onCompositionStart";
							break b;
						case "compositionend":
							y = "onCompositionEnd";
							break b;
						case "compositionupdate":
							y = "onCompositionUpdate";
							break b;
					}
					y = void 0;
				}
				else R ? lr(e, n) && (y = "onCompositionEnd") : e === "keydown" && n.keyCode === 229 && (y = "onCompositionStart");
				y && (or && n.locale !== "ko" && (R || y !== "onCompositionStart" ? y === "onCompositionEnd" && R && (v = Dn()) : (wn = i, Tn = "value" in wn ? wn.value : wn.textContent, R = !0)), _ = hi(r, y), 0 < _.length && (y = new Gn(y, e, null, n, i), o.push({
					event: y,
					listeners: _
				}), v ? y.data = v : (v = ur(n), v !== null && (y.data = v)))), (v = ar ? dr(e, n) : fr(e, n)) && (r = hi(r, "onBeforeInput"), 0 < r.length && (i = new Gn("onBeforeInput", "beforeinput", null, n, i), o.push({
					event: i,
					listeners: r
				}), i.data = v));
			}
			si(o, t);
		});
	}
	function mi(e, t, n) {
		return {
			instance: e,
			listener: t,
			currentTarget: n
		};
	}
	function hi(e, t) {
		for (var n = t + "Capture", r = []; e !== null;) {
			var i = e, a = i.stateNode;
			i.tag === 5 && a !== null && (i = a, a = $e(e, n), a != null && r.unshift(mi(e, a, i)), a = $e(e, t), a != null && r.push(mi(e, a, i))), e = e.return;
		}
		return r;
	}
	function gi(e) {
		if (e === null) return null;
		do
			e = e.return;
		while (e && e.tag !== 5);
		return e || null;
	}
	function _i(e, t, n, r, i) {
		for (var a = t._reactName, o = []; n !== null && n !== r;) {
			var s = n, c = s.alternate, l = s.stateNode;
			if (c !== null && c === r) break;
			s.tag === 5 && l !== null && (s = l, i ? (c = $e(n, a), c != null && o.unshift(mi(n, c, s))) : i || (c = $e(n, a), c != null && o.push(mi(n, c, s)))), n = n.return;
		}
		o.length !== 0 && e.push({
			event: t,
			listeners: o
		});
	}
	var vi = /\r\n?/g, yi = /\u0000|\uFFFD/g;
	function bi(e) {
		return (typeof e == "string" ? e : "" + e).replace(vi, "\n").replace(yi, "");
	}
	function xi(e, t, n) {
		if (t = bi(t), bi(e) !== t && n) throw Error(r(425));
	}
	function Si() {}
	var Ci = null, wi = null;
	function Ti(e, t) {
		return e === "textarea" || e === "noscript" || typeof t.children == "string" || typeof t.children == "number" || typeof t.dangerouslySetInnerHTML == "object" && t.dangerouslySetInnerHTML !== null && t.dangerouslySetInnerHTML.__html != null;
	}
	var Ei = typeof setTimeout == "function" ? setTimeout : void 0, Di = typeof clearTimeout == "function" ? clearTimeout : void 0, Oi = typeof Promise == "function" ? Promise : void 0, ki = typeof queueMicrotask == "function" ? queueMicrotask : Oi === void 0 ? Ei : function(e) {
		return Oi.resolve(null).then(e).catch(Ai);
	};
	function Ai(e) {
		setTimeout(function() {
			throw e;
		});
	}
	function ji(e, t) {
		var n = t, r = 0;
		do {
			var i = n.nextSibling;
			if (e.removeChild(n), i && i.nodeType === 8) if (n = i.data, n === "/$") {
				if (r === 0) {
					e.removeChild(i), hn(t);
					return;
				}
				r--;
			} else n !== "$" && n !== "$?" && n !== "$!" || r++;
			n = i;
		} while (n);
		hn(t);
	}
	function Mi(e) {
		for (; e != null; e = e.nextSibling) {
			var t = e.nodeType;
			if (t === 1 || t === 3) break;
			if (t === 8) {
				if (t = e.data, t === "$" || t === "$!" || t === "$?") break;
				if (t === "/$") return null;
			}
		}
		return e;
	}
	function Ni(e) {
		e = e.previousSibling;
		for (var t = 0; e;) {
			if (e.nodeType === 8) {
				var n = e.data;
				if (n === "$" || n === "$!" || n === "$?") {
					if (t === 0) return e;
					t--;
				} else n === "/$" && t++;
			}
			e = e.previousSibling;
		}
		return null;
	}
	var Pi = Math.random().toString(36).slice(2), Fi = "__reactFiber$" + Pi, Ii = "__reactProps$" + Pi, Li = "__reactContainer$" + Pi, Ri = "__reactEvents$" + Pi, zi = "__reactListeners$" + Pi, Bi = "__reactHandles$" + Pi;
	function Vi(e) {
		var t = e[Fi];
		if (t) return t;
		for (var n = e.parentNode; n;) {
			if (t = n[Li] || n[Fi]) {
				if (n = t.alternate, t.child !== null || n !== null && n.child !== null) for (e = Ni(e); e !== null;) {
					if (n = e[Fi]) return n;
					e = Ni(e);
				}
				return t;
			}
			e = n, n = e.parentNode;
		}
		return null;
	}
	function Hi(e) {
		return e = e[Fi] || e[Li], !e || e.tag !== 5 && e.tag !== 6 && e.tag !== 13 && e.tag !== 3 ? null : e;
	}
	function Ui(e) {
		if (e.tag === 5 || e.tag === 6) return e.stateNode;
		throw Error(r(33));
	}
	function Wi(e) {
		return e[Ii] || null;
	}
	var Gi = [], Ki = -1;
	function qi(e) {
		return { current: e };
	}
	function V(e) {
		0 > Ki || (e.current = Gi[Ki], Gi[Ki] = null, Ki--);
	}
	function H(e, t) {
		Ki++, Gi[Ki] = e.current, e.current = t;
	}
	var Ji = {}, Yi = qi(Ji), Xi = qi(!1), Zi = Ji;
	function Qi(e, t) {
		var n = e.type.contextTypes;
		if (!n) return Ji;
		var r = e.stateNode;
		if (r && r.__reactInternalMemoizedUnmaskedChildContext === t) return r.__reactInternalMemoizedMaskedChildContext;
		var i = {}, a;
		for (a in n) i[a] = t[a];
		return r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = t, e.__reactInternalMemoizedMaskedChildContext = i), i;
	}
	function $i(e) {
		return e = e.childContextTypes, e != null;
	}
	function ea() {
		V(Xi), V(Yi);
	}
	function ta(e, t, n) {
		if (Yi.current !== Ji) throw Error(r(168));
		H(Yi, t), H(Xi, n);
	}
	function na(e, t, n) {
		var i = e.stateNode;
		if (t = t.childContextTypes, typeof i.getChildContext != "function") return n;
		for (var a in i = i.getChildContext(), i) if (!(a in t)) throw Error(r(108, ue(e) || "Unknown", a));
		return F({}, n, i);
	}
	function ra(e) {
		return e = (e = e.stateNode) && e.__reactInternalMemoizedMergedChildContext || Ji, Zi = Yi.current, H(Yi, e), H(Xi, Xi.current), !0;
	}
	function ia(e, t, n) {
		var i = e.stateNode;
		if (!i) throw Error(r(169));
		n ? (e = na(e, t, Zi), i.__reactInternalMemoizedMergedChildContext = e, V(Xi), V(Yi), H(Yi, e)) : V(Xi), H(Xi, n);
	}
	var aa = null, oa = !1, sa = !1;
	function ca(e) {
		aa === null ? aa = [e] : aa.push(e);
	}
	function la(e) {
		oa = !0, ca(e);
	}
	function ua() {
		if (!sa && aa !== null) {
			sa = !0;
			var e = 0, t = L;
			try {
				var n = aa;
				for (L = 1; e < n.length; e++) {
					var r = n[e];
					do
						r = r(!0);
					while (r !== null);
				}
				aa = null, oa = !1;
			} catch (t) {
				throw aa !== null && (aa = aa.slice(e + 1)), gt(St, ua), t;
			} finally {
				L = t, sa = !1;
			}
		}
		return null;
	}
	var da = [], fa = 0, pa = null, ma = 0, ha = [], ga = 0, _a = null, va = 1, ya = "";
	function ba(e, t) {
		da[fa++] = ma, da[fa++] = pa, pa = e, ma = t;
	}
	function xa(e, t, n) {
		ha[ga++] = va, ha[ga++] = ya, ha[ga++] = _a, _a = e;
		var r = va;
		e = ya;
		var i = 32 - I(r) - 1;
		r &= ~(1 << i), n += 1;
		var a = 32 - I(t) + i;
		if (30 < a) {
			var o = i - i % 5;
			a = (r & (1 << o) - 1).toString(32), r >>= o, i -= o, va = 1 << 32 - I(t) + i | n << i | r, ya = a + e;
		} else va = 1 << a | n << i | r, ya = e;
	}
	function Sa(e) {
		e.return !== null && (ba(e, 1), xa(e, 1, 0));
	}
	function Ca(e) {
		for (; e === pa;) pa = da[--fa], da[fa] = null, ma = da[--fa], da[fa] = null;
		for (; e === _a;) _a = ha[--ga], ha[ga] = null, ya = ha[--ga], ha[ga] = null, va = ha[--ga], ha[ga] = null;
	}
	var wa = null, Ta = null, U = !1, Ea = null;
	function Da(e, t) {
		var n = Yl(5, null, null, 0);
		n.elementType = "DELETED", n.stateNode = t, n.return = e, t = e.deletions, t === null ? (e.deletions = [n], e.flags |= 16) : t.push(n);
	}
	function Oa(e, t) {
		switch (e.tag) {
			case 5:
				var n = e.type;
				return t = t.nodeType !== 1 || n.toLowerCase() !== t.nodeName.toLowerCase() ? null : t, t === null ? !1 : (e.stateNode = t, wa = e, Ta = Mi(t.firstChild), !0);
			case 6: return t = e.pendingProps === "" || t.nodeType !== 3 ? null : t, t === null ? !1 : (e.stateNode = t, wa = e, Ta = null, !0);
			case 13: return t = t.nodeType === 8 ? t : null, t === null ? !1 : (n = _a === null ? null : {
				id: va,
				overflow: ya
			}, e.memoizedState = {
				dehydrated: t,
				treeContext: n,
				retryLane: 1073741824
			}, n = Yl(18, null, null, 0), n.stateNode = t, n.return = e, e.child = n, wa = e, Ta = null, !0);
			default: return !1;
		}
	}
	function W(e) {
		return (e.mode & 1) != 0 && (e.flags & 128) == 0;
	}
	function ka(e) {
		if (U) {
			var t = Ta;
			if (t) {
				var n = t;
				if (!Oa(e, t)) {
					if (W(e)) throw Error(r(418));
					t = Mi(n.nextSibling);
					var i = wa;
					t && Oa(e, t) ? Da(i, n) : (e.flags = e.flags & -4097 | 2, U = !1, wa = e);
				}
			} else {
				if (W(e)) throw Error(r(418));
				e.flags = e.flags & -4097 | 2, U = !1, wa = e;
			}
		}
	}
	function Aa(e) {
		for (e = e.return; e !== null && e.tag !== 5 && e.tag !== 3 && e.tag !== 13;) e = e.return;
		wa = e;
	}
	function ja(e) {
		if (e !== wa) return !1;
		if (!U) return Aa(e), U = !0, !1;
		var t;
		if ((t = e.tag !== 3) && !(t = e.tag !== 5) && (t = e.type, t = t !== "head" && t !== "body" && !Ti(e.type, e.memoizedProps)), t && (t = Ta)) {
			if (W(e)) throw Ma(), Error(r(418));
			for (; t;) Da(e, t), t = Mi(t.nextSibling);
		}
		if (Aa(e), e.tag === 13) {
			if (e = e.memoizedState, e = e === null ? null : e.dehydrated, !e) throw Error(r(317));
			a: {
				for (e = e.nextSibling, t = 0; e;) {
					if (e.nodeType === 8) {
						var n = e.data;
						if (n === "/$") {
							if (t === 0) {
								Ta = Mi(e.nextSibling);
								break a;
							}
							t--;
						} else n !== "$" && n !== "$!" && n !== "$?" || t++;
					}
					e = e.nextSibling;
				}
				Ta = null;
			}
		} else Ta = wa ? Mi(e.stateNode.nextSibling) : null;
		return !0;
	}
	function Ma() {
		for (var e = Ta; e;) e = Mi(e.nextSibling);
	}
	function Na() {
		Ta = wa = null, U = !1;
	}
	function Pa(e) {
		Ea === null ? Ea = [e] : Ea.push(e);
	}
	var Fa = C.ReactCurrentBatchConfig;
	function Ia(e, t, n) {
		if (e = n.ref, e !== null && typeof e != "function" && typeof e != "object") {
			if (n._owner) {
				if (n = n._owner, n) {
					if (n.tag !== 1) throw Error(r(309));
					var i = n.stateNode;
				}
				if (!i) throw Error(r(147, e));
				var a = i, o = "" + e;
				return t !== null && t.ref !== null && typeof t.ref == "function" && t.ref._stringRef === o ? t.ref : (t = function(e) {
					var t = a.refs;
					e === null ? delete t[o] : t[o] = e;
				}, t._stringRef = o, t);
			}
			if (typeof e != "string") throw Error(r(284));
			if (!n._owner) throw Error(r(290, e));
		}
		return e;
	}
	function La(e, t) {
		throw e = Object.prototype.toString.call(t), Error(r(31, e === "[object Object]" ? "object with keys {" + Object.keys(t).join(", ") + "}" : e));
	}
	function Ra(e) {
		var t = e._init;
		return t(e._payload);
	}
	function za(e) {
		function t(t, n) {
			if (e) {
				var r = t.deletions;
				r === null ? (t.deletions = [n], t.flags |= 16) : r.push(n);
			}
		}
		function n(n, r) {
			if (!e) return null;
			for (; r !== null;) t(n, r), r = r.sibling;
			return null;
		}
		function i(e, t) {
			for (e = /* @__PURE__ */ new Map(); t !== null;) t.key === null ? e.set(t.index, t) : e.set(t.key, t), t = t.sibling;
			return e;
		}
		function a(e, t) {
			return e = Ql(e, t), e.index = 0, e.sibling = null, e;
		}
		function o(t, n, r) {
			return t.index = r, e ? (r = t.alternate, r === null ? (t.flags |= 2, n) : (r = r.index, r < n ? (t.flags |= 2, n) : r)) : (t.flags |= 1048576, n);
		}
		function s(t) {
			return e && t.alternate === null && (t.flags |= 2), t;
		}
		function c(e, t, n, r) {
			return t === null || t.tag !== 6 ? (t = nu(n, e.mode, r), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function l(e, t, n, r) {
			var i = n.type;
			return i === E ? d(e, t, n.props.children, r, n.key) : t !== null && (t.elementType === i || typeof i == "object" && i && i.$$typeof === ee && Ra(i) === t.type) ? (r = a(t, n.props), r.ref = Ia(e, t, n), r.return = e, r) : (r = $l(n.type, n.key, n.props, null, e.mode, r), r.ref = Ia(e, t, n), r.return = e, r);
		}
		function u(e, t, n, r) {
			return t === null || t.tag !== 4 || t.stateNode.containerInfo !== n.containerInfo || t.stateNode.implementation !== n.implementation ? (t = ru(n, e.mode, r), t.return = e, t) : (t = a(t, n.children || []), t.return = e, t);
		}
		function d(e, t, n, r, i) {
			return t === null || t.tag !== 7 ? (t = eu(n, e.mode, r, i), t.return = e, t) : (t = a(t, n), t.return = e, t);
		}
		function f(e, t, n) {
			if (typeof t == "string" && t !== "" || typeof t == "number") return t = nu("" + t, e.mode, n), t.return = e, t;
			if (typeof t == "object" && t) {
				switch (t.$$typeof) {
					case w: return n = $l(t.type, t.key, t.props, null, e.mode, n), n.ref = Ia(e, null, t), n.return = e, n;
					case T: return t = ru(t, e.mode, n), t.return = e, t;
					case ee:
						var r = t._init;
						return f(e, r(t._payload), n);
				}
				if (Ce(t) || re(t)) return t = eu(t, e.mode, n, null), t.return = e, t;
				La(e, t);
			}
			return null;
		}
		function p(e, t, n, r) {
			var i = t === null ? null : t.key;
			if (typeof n == "string" && n !== "" || typeof n == "number") return i === null ? c(e, t, "" + n, r) : null;
			if (typeof n == "object" && n) {
				switch (n.$$typeof) {
					case w: return n.key === i ? l(e, t, n, r) : null;
					case T: return n.key === i ? u(e, t, n, r) : null;
					case ee: return i = n._init, p(e, t, i(n._payload), r);
				}
				if (Ce(n) || re(n)) return i === null ? d(e, t, n, r, null) : null;
				La(e, n);
			}
			return null;
		}
		function m(e, t, n, r, i) {
			if (typeof r == "string" && r !== "" || typeof r == "number") return e = e.get(n) || null, c(t, e, "" + r, i);
			if (typeof r == "object" && r) {
				switch (r.$$typeof) {
					case w: return e = e.get(r.key === null ? n : r.key) || null, l(t, e, r, i);
					case T: return e = e.get(r.key === null ? n : r.key) || null, u(t, e, r, i);
					case ee:
						var a = r._init;
						return m(e, t, n, a(r._payload), i);
				}
				if (Ce(r) || re(r)) return e = e.get(n) || null, d(t, e, r, i, null);
				La(t, r);
			}
			return null;
		}
		function h(r, a, s, c) {
			for (var l = null, u = null, d = a, h = a = 0, g = null; d !== null && h < s.length; h++) {
				d.index > h ? (g = d, d = null) : g = d.sibling;
				var _ = p(r, d, s[h], c);
				if (_ === null) {
					d === null && (d = g);
					break;
				}
				e && d && _.alternate === null && t(r, d), a = o(_, a, h), u === null ? l = _ : u.sibling = _, u = _, d = g;
			}
			if (h === s.length) return n(r, d), U && ba(r, h), l;
			if (d === null) {
				for (; h < s.length; h++) d = f(r, s[h], c), d !== null && (a = o(d, a, h), u === null ? l = d : u.sibling = d, u = d);
				return U && ba(r, h), l;
			}
			for (d = i(r, d); h < s.length; h++) g = m(d, r, h, s[h], c), g !== null && (e && g.alternate !== null && d.delete(g.key === null ? h : g.key), a = o(g, a, h), u === null ? l = g : u.sibling = g, u = g);
			return e && d.forEach(function(e) {
				return t(r, e);
			}), U && ba(r, h), l;
		}
		function g(a, s, c, l) {
			var u = re(c);
			if (typeof u != "function") throw Error(r(150));
			if (c = u.call(c), c == null) throw Error(r(151));
			for (var d = u = null, h = s, g = s = 0, _ = null, v = c.next(); h !== null && !v.done; g++, v = c.next()) {
				h.index > g ? (_ = h, h = null) : _ = h.sibling;
				var y = p(a, h, v.value, l);
				if (y === null) {
					h === null && (h = _);
					break;
				}
				e && h && y.alternate === null && t(a, h), s = o(y, s, g), d === null ? u = y : d.sibling = y, d = y, h = _;
			}
			if (v.done) return n(a, h), U && ba(a, g), u;
			if (h === null) {
				for (; !v.done; g++, v = c.next()) v = f(a, v.value, l), v !== null && (s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
				return U && ba(a, g), u;
			}
			for (h = i(a, h); !v.done; g++, v = c.next()) v = m(h, a, g, v.value, l), v !== null && (e && v.alternate !== null && h.delete(v.key === null ? g : v.key), s = o(v, s, g), d === null ? u = v : d.sibling = v, d = v);
			return e && h.forEach(function(e) {
				return t(a, e);
			}), U && ba(a, g), u;
		}
		function _(e, r, i, o) {
			if (typeof i == "object" && i && i.type === E && i.key === null && (i = i.props.children), typeof i == "object" && i) {
				switch (i.$$typeof) {
					case w:
						a: {
							for (var c = i.key, l = r; l !== null;) {
								if (l.key === c) {
									if (c = i.type, c === E) {
										if (l.tag === 7) {
											n(e, l.sibling), r = a(l, i.props.children), r.return = e, e = r;
											break a;
										}
									} else if (l.elementType === c || typeof c == "object" && c && c.$$typeof === ee && Ra(c) === l.type) {
										n(e, l.sibling), r = a(l, i.props), r.ref = Ia(e, l, i), r.return = e, e = r;
										break a;
									}
									n(e, l);
									break;
								} else t(e, l);
								l = l.sibling;
							}
							i.type === E ? (r = eu(i.props.children, e.mode, o, i.key), r.return = e, e = r) : (o = $l(i.type, i.key, i.props, null, e.mode, o), o.ref = Ia(e, r, i), o.return = e, e = o);
						}
						return s(e);
					case T:
						a: {
							for (l = i.key; r !== null;) {
								if (r.key === l) if (r.tag === 4 && r.stateNode.containerInfo === i.containerInfo && r.stateNode.implementation === i.implementation) {
									n(e, r.sibling), r = a(r, i.children || []), r.return = e, e = r;
									break a;
								} else {
									n(e, r);
									break;
								}
								else t(e, r);
								r = r.sibling;
							}
							r = ru(i, e.mode, o), r.return = e, e = r;
						}
						return s(e);
					case ee: return l = i._init, _(e, r, l(i._payload), o);
				}
				if (Ce(i)) return h(e, r, i, o);
				if (re(i)) return g(e, r, i, o);
				La(e, i);
			}
			return typeof i == "string" && i !== "" || typeof i == "number" ? (i = "" + i, r !== null && r.tag === 6 ? (n(e, r.sibling), r = a(r, i), r.return = e, e = r) : (n(e, r), r = nu(i, e.mode, o), r.return = e, e = r), s(e)) : n(e, r);
		}
		return _;
	}
	var G = za(!0), Ba = za(!1), Va = qi(null), Ha = null, Ua = null, Wa = null;
	function Ga() {
		Wa = Ua = Ha = null;
	}
	function Ka(e) {
		var t = Va.current;
		V(Va), e._currentValue = t;
	}
	function qa(e, t, n) {
		for (; e !== null;) {
			var r = e.alternate;
			if ((e.childLanes & t) === t ? r !== null && (r.childLanes & t) !== t && (r.childLanes |= t) : (e.childLanes |= t, r !== null && (r.childLanes |= t)), e === n) break;
			e = e.return;
		}
	}
	function Ja(e, t) {
		Ha = e, Wa = Ua = null, e = e.dependencies, e !== null && e.firstContext !== null && ((e.lanes & t) !== 0 && (Is = !0), e.firstContext = null);
	}
	function Ya(e) {
		var t = e._currentValue;
		if (Wa !== e) if (e = {
			context: e,
			memoizedValue: t,
			next: null
		}, Ua === null) {
			if (Ha === null) throw Error(r(308));
			Ua = e, Ha.dependencies = {
				lanes: 0,
				firstContext: e
			};
		} else Ua = Ua.next = e;
		return t;
	}
	var Xa = null;
	function Za(e) {
		Xa === null ? Xa = [e] : Xa.push(e);
	}
	function Qa(e, t, n, r) {
		var i = t.interleaved;
		return i === null ? (n.next = n, Za(t)) : (n.next = i.next, i.next = n), t.interleaved = n, $a(e, r);
	}
	function $a(e, t) {
		e.lanes |= t;
		var n = e.alternate;
		for (n !== null && (n.lanes |= t), n = e, e = e.return; e !== null;) e.childLanes |= t, n = e.alternate, n !== null && (n.childLanes |= t), n = e, e = e.return;
		return n.tag === 3 ? n.stateNode : null;
	}
	var eo = !1;
	function to(e) {
		e.updateQueue = {
			baseState: e.memoizedState,
			firstBaseUpdate: null,
			lastBaseUpdate: null,
			shared: {
				pending: null,
				interleaved: null,
				lanes: 0
			},
			effects: null
		};
	}
	function no(e, t) {
		e = e.updateQueue, t.updateQueue === e && (t.updateQueue = {
			baseState: e.baseState,
			firstBaseUpdate: e.firstBaseUpdate,
			lastBaseUpdate: e.lastBaseUpdate,
			shared: e.shared,
			effects: e.effects
		});
	}
	function ro(e, t) {
		return {
			eventTime: e,
			lane: t,
			tag: 0,
			payload: null,
			callback: null,
			next: null
		};
	}
	function io(e, t, n) {
		var r = e.updateQueue;
		if (r === null) return null;
		if (r = r.shared, X & 2) {
			var i = r.pending;
			return i === null ? t.next = t : (t.next = i.next, i.next = t), r.pending = t, $a(e, n);
		}
		return i = r.interleaved, i === null ? (t.next = t, Za(r)) : (t.next = i.next, i.next = t), r.interleaved = t, $a(e, n);
	}
	function ao(e, t, n) {
		if (t = t.updateQueue, t !== null && (t = t.shared, n & 4194240)) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Wt(e, n);
		}
	}
	function oo(e, t) {
		var n = e.updateQueue, r = e.alternate;
		if (r !== null && (r = r.updateQueue, n === r)) {
			var i = null, a = null;
			if (n = n.firstBaseUpdate, n !== null) {
				do {
					var o = {
						eventTime: n.eventTime,
						lane: n.lane,
						tag: n.tag,
						payload: n.payload,
						callback: n.callback,
						next: null
					};
					a === null ? i = a = o : a = a.next = o, n = n.next;
				} while (n !== null);
				a === null ? i = a = t : a = a.next = t;
			} else i = a = t;
			n = {
				baseState: r.baseState,
				firstBaseUpdate: i,
				lastBaseUpdate: a,
				shared: r.shared,
				effects: r.effects
			}, e.updateQueue = n;
			return;
		}
		e = n.lastBaseUpdate, e === null ? n.firstBaseUpdate = t : e.next = t, n.lastBaseUpdate = t;
	}
	function so(e, t, n, r) {
		var i = e.updateQueue;
		eo = !1;
		var a = i.firstBaseUpdate, o = i.lastBaseUpdate, s = i.shared.pending;
		if (s !== null) {
			i.shared.pending = null;
			var c = s, l = c.next;
			c.next = null, o === null ? a = l : o.next = l, o = c;
			var u = e.alternate;
			u !== null && (u = u.updateQueue, s = u.lastBaseUpdate, s !== o && (s === null ? u.firstBaseUpdate = l : s.next = l, u.lastBaseUpdate = c));
		}
		if (a !== null) {
			var d = i.baseState;
			o = 0, u = l = c = null, s = a;
			do {
				var f = s.lane, p = s.eventTime;
				if ((r & f) === f) {
					u !== null && (u = u.next = {
						eventTime: p,
						lane: 0,
						tag: s.tag,
						payload: s.payload,
						callback: s.callback,
						next: null
					});
					a: {
						var m = e, h = s;
						switch (f = t, p = n, h.tag) {
							case 1:
								if (m = h.payload, typeof m == "function") {
									d = m.call(p, d, f);
									break a;
								}
								d = m;
								break a;
							case 3: m.flags = m.flags & -65537 | 128;
							case 0:
								if (m = h.payload, f = typeof m == "function" ? m.call(p, d, f) : m, f == null) break a;
								d = F({}, d, f);
								break a;
							case 2: eo = !0;
						}
					}
					s.callback !== null && s.lane !== 0 && (e.flags |= 64, f = i.effects, f === null ? i.effects = [s] : f.push(s));
				} else p = {
					eventTime: p,
					lane: f,
					tag: s.tag,
					payload: s.payload,
					callback: s.callback,
					next: null
				}, u === null ? (l = u = p, c = d) : u = u.next = p, o |= f;
				if (s = s.next, s === null) {
					if (s = i.shared.pending, s === null) break;
					f = s, s = f.next, f.next = null, i.lastBaseUpdate = f, i.shared.pending = null;
				}
			} while (1);
			if (u === null && (c = d), i.baseState = c, i.firstBaseUpdate = l, i.lastBaseUpdate = u, t = i.shared.interleaved, t !== null) {
				i = t;
				do
					o |= i.lane, i = i.next;
				while (i !== t);
			} else a === null && (i.shared.lanes = 0);
			Zc |= o, e.lanes = o, e.memoizedState = d;
		}
	}
	function co(e, t, n) {
		if (e = t.effects, t.effects = null, e !== null) for (t = 0; t < e.length; t++) {
			var i = e[t], a = i.callback;
			if (a !== null) {
				if (i.callback = null, i = n, typeof a != "function") throw Error(r(191, a));
				a.call(i);
			}
		}
	}
	var lo = {}, uo = qi(lo), fo = qi(lo), po = qi(lo);
	function mo(e) {
		if (e === lo) throw Error(r(174));
		return e;
	}
	function ho(e, t) {
		switch (H(po, t), H(fo, e), H(uo, lo), e = t.nodeType, e) {
			case 9:
			case 11:
				t = (t = t.documentElement) ? t.namespaceURI : Ae(null, "");
				break;
			default: e = e === 8 ? t.parentNode : t, t = e.namespaceURI || null, e = e.tagName, t = Ae(t, e);
		}
		V(uo), H(uo, t);
	}
	function go() {
		V(uo), V(fo), V(po);
	}
	function _o(e) {
		mo(po.current);
		var t = mo(uo.current), n = Ae(t, e.type);
		t !== n && (H(fo, e), H(uo, n));
	}
	function vo(e) {
		fo.current === e && (V(uo), V(fo));
	}
	var yo = qi(0);
	function bo(e) {
		for (var t = e; t !== null;) {
			if (t.tag === 13) {
				var n = t.memoizedState;
				if (n !== null && (n = n.dehydrated, n === null || n.data === "$?" || n.data === "$!")) return t;
			} else if (t.tag === 19 && t.memoizedProps.revealOrder !== void 0) {
				if (t.flags & 128) return t;
			} else if (t.child !== null) {
				t.child.return = t, t = t.child;
				continue;
			}
			if (t === e) break;
			for (; t.sibling === null;) {
				if (t.return === null || t.return === e) return null;
				t = t.return;
			}
			t.sibling.return = t.return, t = t.sibling;
		}
		return null;
	}
	var xo = [];
	function So() {
		for (var e = 0; e < xo.length; e++) xo[e]._workInProgressVersionPrimary = null;
		xo.length = 0;
	}
	var Co = C.ReactCurrentDispatcher, wo = C.ReactCurrentBatchConfig, To = 0, K = null, Eo = null, Do = null, Oo = !1, ko = !1, Ao = 0, jo = 0;
	function Mo() {
		throw Error(r(321));
	}
	function No(e, t) {
		if (t === null) return !1;
		for (var n = 0; n < t.length && n < e.length; n++) if (!B(e[n], t[n])) return !1;
		return !0;
	}
	function Po(e, t, n, i, a, o) {
		if (To = o, K = t, t.memoizedState = null, t.updateQueue = null, t.lanes = 0, Co.current = e === null || e.memoizedState === null ? gs : _s, e = n(i, a), ko) {
			o = 0;
			do {
				if (ko = !1, Ao = 0, 25 <= o) throw Error(r(301));
				o += 1, Do = Eo = null, t.updateQueue = null, Co.current = vs, e = n(i, a);
			} while (ko);
		}
		if (Co.current = hs, t = Eo !== null && Eo.next !== null, To = 0, Do = Eo = K = null, Oo = !1, t) throw Error(r(300));
		return e;
	}
	function Fo() {
		var e = Ao !== 0;
		return Ao = 0, e;
	}
	function Io() {
		var e = {
			memoizedState: null,
			baseState: null,
			baseQueue: null,
			queue: null,
			next: null
		};
		return Do === null ? K.memoizedState = Do = e : Do = Do.next = e, Do;
	}
	function Lo() {
		if (Eo === null) {
			var e = K.alternate;
			e = e === null ? null : e.memoizedState;
		} else e = Eo.next;
		var t = Do === null ? K.memoizedState : Do.next;
		if (t !== null) Do = t, Eo = e;
		else {
			if (e === null) throw Error(r(310));
			Eo = e, e = {
				memoizedState: Eo.memoizedState,
				baseState: Eo.baseState,
				baseQueue: Eo.baseQueue,
				queue: Eo.queue,
				next: null
			}, Do === null ? K.memoizedState = Do = e : Do = Do.next = e;
		}
		return Do;
	}
	function Ro(e, t) {
		return typeof t == "function" ? t(e) : t;
	}
	function zo(e) {
		var t = Lo(), n = t.queue;
		if (n === null) throw Error(r(311));
		n.lastRenderedReducer = e;
		var i = Eo, a = i.baseQueue, o = n.pending;
		if (o !== null) {
			if (a !== null) {
				var s = a.next;
				a.next = o.next, o.next = s;
			}
			i.baseQueue = a = o, n.pending = null;
		}
		if (a !== null) {
			o = a.next, i = i.baseState;
			var c = s = null, l = null, u = o;
			do {
				var d = u.lane;
				if ((To & d) === d) l !== null && (l = l.next = {
					lane: 0,
					action: u.action,
					hasEagerState: u.hasEagerState,
					eagerState: u.eagerState,
					next: null
				}), i = u.hasEagerState ? u.eagerState : e(i, u.action);
				else {
					var f = {
						lane: d,
						action: u.action,
						hasEagerState: u.hasEagerState,
						eagerState: u.eagerState,
						next: null
					};
					l === null ? (c = l = f, s = i) : l = l.next = f, K.lanes |= d, Zc |= d;
				}
				u = u.next;
			} while (u !== null && u !== o);
			l === null ? s = i : l.next = c, B(i, t.memoizedState) || (Is = !0), t.memoizedState = i, t.baseState = s, t.baseQueue = l, n.lastRenderedState = i;
		}
		if (e = n.interleaved, e !== null) {
			a = e;
			do
				o = a.lane, K.lanes |= o, Zc |= o, a = a.next;
			while (a !== e);
		} else a === null && (n.lanes = 0);
		return [t.memoizedState, n.dispatch];
	}
	function Bo(e) {
		var t = Lo(), n = t.queue;
		if (n === null) throw Error(r(311));
		n.lastRenderedReducer = e;
		var i = n.dispatch, a = n.pending, o = t.memoizedState;
		if (a !== null) {
			n.pending = null;
			var s = a = a.next;
			do
				o = e(o, s.action), s = s.next;
			while (s !== a);
			B(o, t.memoizedState) || (Is = !0), t.memoizedState = o, t.baseQueue === null && (t.baseState = o), n.lastRenderedState = o;
		}
		return [o, i];
	}
	function Vo() {}
	function Ho(e, t) {
		var n = K, i = Lo(), a = t(), o = !B(i.memoizedState, a);
		if (o && (i.memoizedState = a, Is = !0), i = i.queue, $o(Go.bind(null, n, i, e), [e]), i.getSnapshot !== t || o || Do !== null && Do.memoizedState.tag & 1) {
			if (n.flags |= 2048, Yo(9, Wo.bind(null, n, i, a, t), void 0, null), Wc === null) throw Error(r(349));
			To & 30 || Uo(n, t, a);
		}
		return a;
	}
	function Uo(e, t, n) {
		e.flags |= 16384, e = {
			getSnapshot: t,
			value: n
		}, t = K.updateQueue, t === null ? (t = {
			lastEffect: null,
			stores: null
		}, K.updateQueue = t, t.stores = [e]) : (n = t.stores, n === null ? t.stores = [e] : n.push(e));
	}
	function Wo(e, t, n, r) {
		t.value = n, t.getSnapshot = r, Ko(t) && qo(e);
	}
	function Go(e, t, n) {
		return n(function() {
			Ko(t) && qo(e);
		});
	}
	function Ko(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !B(e, n);
		} catch (e) {
			return !0;
		}
	}
	function qo(e) {
		var t = $a(e, 1);
		t !== null && _l(t, e, 1, -1);
	}
	function Jo(e) {
		var t = Io();
		return typeof e == "function" && (e = e()), t.memoizedState = t.baseState = e, e = {
			pending: null,
			interleaved: null,
			lanes: 0,
			dispatch: null,
			lastRenderedReducer: Ro,
			lastRenderedState: e
		}, t.queue = e, e = e.dispatch = ds.bind(null, K, e), [t.memoizedState, e];
	}
	function Yo(e, t, n, r) {
		return e = {
			tag: e,
			create: t,
			destroy: n,
			deps: r,
			next: null
		}, t = K.updateQueue, t === null ? (t = {
			lastEffect: null,
			stores: null
		}, K.updateQueue = t, t.lastEffect = e.next = e) : (n = t.lastEffect, n === null ? t.lastEffect = e.next = e : (r = n.next, n.next = e, e.next = r, t.lastEffect = e)), e;
	}
	function q() {
		return Lo().memoizedState;
	}
	function Xo(e, t, n, r) {
		var i = Io();
		K.flags |= e, i.memoizedState = Yo(1 | t, n, void 0, r === void 0 ? null : r);
	}
	function Zo(e, t, n, r) {
		var i = Lo();
		r = r === void 0 ? null : r;
		var a = void 0;
		if (Eo !== null) {
			var o = Eo.memoizedState;
			if (a = o.destroy, r !== null && No(r, o.deps)) {
				i.memoizedState = Yo(t, n, a, r);
				return;
			}
		}
		K.flags |= e, i.memoizedState = Yo(1 | t, n, a, r);
	}
	function Qo(e, t) {
		return Xo(8390656, 8, e, t);
	}
	function $o(e, t) {
		return Zo(2048, 8, e, t);
	}
	function es(e, t) {
		return Zo(4, 2, e, t);
	}
	function ts(e, t) {
		return Zo(4, 4, e, t);
	}
	function ns(e, t) {
		if (typeof t == "function") return e = e(), t(e), function() {
			t(null);
		};
		if (t != null) return e = e(), t.current = e, function() {
			t.current = null;
		};
	}
	function rs(e, t, n) {
		return n = n == null ? null : n.concat([e]), Zo(4, 4, ns.bind(null, t, e), n);
	}
	function is() {}
	function as(e, t) {
		var n = Lo();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return r !== null && t !== null && No(t, r[1]) ? r[0] : (n.memoizedState = [e, t], e);
	}
	function os(e, t) {
		var n = Lo();
		t = t === void 0 ? null : t;
		var r = n.memoizedState;
		return r !== null && t !== null && No(t, r[1]) ? r[0] : (e = e(), n.memoizedState = [e, t], e);
	}
	function ss(e, t, n) {
		return To & 21 ? (B(n, t) || (n = Bt(), K.lanes |= n, Zc |= n, e.baseState = !0), t) : (e.baseState && (e.baseState = !1, Is = !0), e.memoizedState = n);
	}
	function cs(e, t) {
		var n = L;
		L = n !== 0 && 4 > n ? n : 4, e(!0);
		var r = wo.transition;
		wo.transition = {};
		try {
			e(!1), t();
		} finally {
			L = n, wo.transition = r;
		}
	}
	function ls() {
		return Lo().memoizedState;
	}
	function us(e, t, n) {
		var r = gl(e);
		if (n = {
			lane: r,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		}, fs(e)) ps(t, n);
		else if (n = Qa(e, t, n, r), n !== null) {
			var i = hl();
			_l(n, e, r, i), ms(n, t, r);
		}
	}
	function ds(e, t, n) {
		var r = gl(e), i = {
			lane: r,
			action: n,
			hasEagerState: !1,
			eagerState: null,
			next: null
		};
		if (fs(e)) ps(t, i);
		else {
			var a = e.alternate;
			if (e.lanes === 0 && (a === null || a.lanes === 0) && (a = t.lastRenderedReducer, a !== null)) try {
				var o = t.lastRenderedState, s = a(o, n);
				if (i.hasEagerState = !0, i.eagerState = s, B(s, o)) {
					var c = t.interleaved;
					c === null ? (i.next = i, Za(t)) : (i.next = c.next, c.next = i), t.interleaved = i;
					return;
				}
			} catch (e) {}
			n = Qa(e, t, i, r), n !== null && (i = hl(), _l(n, e, r, i), ms(n, t, r));
		}
	}
	function fs(e) {
		var t = e.alternate;
		return e === K || t !== null && t === K;
	}
	function ps(e, t) {
		ko = Oo = !0;
		var n = e.pending;
		n === null ? t.next = t : (t.next = n.next, n.next = t), e.pending = t;
	}
	function ms(e, t, n) {
		if (n & 4194240) {
			var r = t.lanes;
			r &= e.pendingLanes, n |= r, t.lanes = n, Wt(e, n);
		}
	}
	var hs = {
		readContext: Ya,
		useCallback: Mo,
		useContext: Mo,
		useEffect: Mo,
		useImperativeHandle: Mo,
		useInsertionEffect: Mo,
		useLayoutEffect: Mo,
		useMemo: Mo,
		useReducer: Mo,
		useRef: Mo,
		useState: Mo,
		useDebugValue: Mo,
		useDeferredValue: Mo,
		useTransition: Mo,
		useMutableSource: Mo,
		useSyncExternalStore: Mo,
		useId: Mo,
		unstable_isNewReconciler: !1
	}, gs = {
		readContext: Ya,
		useCallback: function(e, t) {
			return Io().memoizedState = [e, t === void 0 ? null : t], e;
		},
		useContext: Ya,
		useEffect: Qo,
		useImperativeHandle: function(e, t, n) {
			return n = n == null ? null : n.concat([e]), Xo(4194308, 4, ns.bind(null, t, e), n);
		},
		useLayoutEffect: function(e, t) {
			return Xo(4194308, 4, e, t);
		},
		useInsertionEffect: function(e, t) {
			return Xo(4, 2, e, t);
		},
		useMemo: function(e, t) {
			var n = Io();
			return t = t === void 0 ? null : t, e = e(), n.memoizedState = [e, t], e;
		},
		useReducer: function(e, t, n) {
			var r = Io();
			return t = n === void 0 ? t : n(t), r.memoizedState = r.baseState = t, e = {
				pending: null,
				interleaved: null,
				lanes: 0,
				dispatch: null,
				lastRenderedReducer: e,
				lastRenderedState: t
			}, r.queue = e, e = e.dispatch = us.bind(null, K, e), [r.memoizedState, e];
		},
		useRef: function(e) {
			var t = Io();
			return e = { current: e }, t.memoizedState = e;
		},
		useState: Jo,
		useDebugValue: is,
		useDeferredValue: function(e) {
			return Io().memoizedState = e;
		},
		useTransition: function() {
			var e = Jo(!1), t = e[0];
			return e = cs.bind(null, e[1]), Io().memoizedState = e, [t, e];
		},
		useMutableSource: function() {},
		useSyncExternalStore: function(e, t, n) {
			var i = K, a = Io();
			if (U) {
				if (n === void 0) throw Error(r(407));
				n = n();
			} else {
				if (n = t(), Wc === null) throw Error(r(349));
				To & 30 || Uo(i, t, n);
			}
			a.memoizedState = n;
			var o = {
				value: n,
				getSnapshot: t
			};
			return a.queue = o, Qo(Go.bind(null, i, o, e), [e]), i.flags |= 2048, Yo(9, Wo.bind(null, i, o, n, t), void 0, null), n;
		},
		useId: function() {
			var e = Io(), t = Wc.identifierPrefix;
			if (U) {
				var n = ya, r = va;
				n = (r & ~(1 << 32 - I(r) - 1)).toString(32) + n, t = ":" + t + "R" + n, n = Ao++, 0 < n && (t += "H" + n.toString(32)), t += ":";
			} else n = jo++, t = ":" + t + "r" + n.toString(32) + ":";
			return e.memoizedState = t;
		},
		unstable_isNewReconciler: !1
	}, _s = {
		readContext: Ya,
		useCallback: as,
		useContext: Ya,
		useEffect: $o,
		useImperativeHandle: rs,
		useInsertionEffect: es,
		useLayoutEffect: ts,
		useMemo: os,
		useReducer: zo,
		useRef: q,
		useState: function() {
			return zo(Ro);
		},
		useDebugValue: is,
		useDeferredValue: function(e) {
			return ss(Lo(), Eo.memoizedState, e);
		},
		useTransition: function() {
			return [zo(Ro)[0], Lo().memoizedState];
		},
		useMutableSource: Vo,
		useSyncExternalStore: Ho,
		useId: ls,
		unstable_isNewReconciler: !1
	}, vs = {
		readContext: Ya,
		useCallback: as,
		useContext: Ya,
		useEffect: $o,
		useImperativeHandle: rs,
		useInsertionEffect: es,
		useLayoutEffect: ts,
		useMemo: os,
		useReducer: Bo,
		useRef: q,
		useState: function() {
			return Bo(Ro);
		},
		useDebugValue: is,
		useDeferredValue: function(e) {
			var t = Lo();
			return Eo === null ? t.memoizedState = e : ss(t, Eo.memoizedState, e);
		},
		useTransition: function() {
			return [Bo(Ro)[0], Lo().memoizedState];
		},
		useMutableSource: Vo,
		useSyncExternalStore: Ho,
		useId: ls,
		unstable_isNewReconciler: !1
	};
	function ys(e, t) {
		if (e && e.defaultProps) {
			for (var n in t = F({}, t), e = e.defaultProps, e) t[n] === void 0 && (t[n] = e[n]);
			return t;
		}
		return t;
	}
	function bs(e, t, n, r) {
		t = e.memoizedState, n = n(r, t), n = n == null ? t : F({}, t, n), e.memoizedState = n, e.lanes === 0 && (e.updateQueue.baseState = n);
	}
	var xs = {
		isMounted: function(e) {
			return (e = e._reactInternals) ? ut(e) === e : !1;
		},
		enqueueSetState: function(e, t, n) {
			e = e._reactInternals;
			var r = hl(), i = gl(e), a = ro(r, i);
			a.payload = t, n != null && (a.callback = n), t = io(e, a, i), t !== null && (_l(t, e, i, r), ao(t, e, i));
		},
		enqueueReplaceState: function(e, t, n) {
			e = e._reactInternals;
			var r = hl(), i = gl(e), a = ro(r, i);
			a.tag = 1, a.payload = t, n != null && (a.callback = n), t = io(e, a, i), t !== null && (_l(t, e, i, r), ao(t, e, i));
		},
		enqueueForceUpdate: function(e, t) {
			e = e._reactInternals;
			var n = hl(), r = gl(e), i = ro(n, r);
			i.tag = 2, t != null && (i.callback = t), t = io(e, i, r), t !== null && (_l(t, e, r, n), ao(t, e, r));
		}
	};
	function Ss(e, t, n, r, i, a, o) {
		return e = e.stateNode, typeof e.shouldComponentUpdate == "function" ? e.shouldComponentUpdate(r, a, o) : t.prototype && t.prototype.isPureReactComponent ? !jr(n, r) || !jr(i, a) : !0;
	}
	function Cs(e, t, n) {
		var r = !1, i = Ji, a = t.contextType;
		return typeof a == "object" && a ? a = Ya(a) : (i = $i(t) ? Zi : Yi.current, r = t.contextTypes, a = (r = r != null) ? Qi(e, i) : Ji), t = new t(n, a), e.memoizedState = t.state !== null && t.state !== void 0 ? t.state : null, t.updater = xs, e.stateNode = t, t._reactInternals = e, r && (e = e.stateNode, e.__reactInternalMemoizedUnmaskedChildContext = i, e.__reactInternalMemoizedMaskedChildContext = a), t;
	}
	function ws(e, t, n, r) {
		e = t.state, typeof t.componentWillReceiveProps == "function" && t.componentWillReceiveProps(n, r), typeof t.UNSAFE_componentWillReceiveProps == "function" && t.UNSAFE_componentWillReceiveProps(n, r), t.state !== e && xs.enqueueReplaceState(t, t.state, null);
	}
	function Ts(e, t, n, r) {
		var i = e.stateNode;
		i.props = n, i.state = e.memoizedState, i.refs = {}, to(e);
		var a = t.contextType;
		typeof a == "object" && a ? i.context = Ya(a) : (a = $i(t) ? Zi : Yi.current, i.context = Qi(e, a)), i.state = e.memoizedState, a = t.getDerivedStateFromProps, typeof a == "function" && (bs(e, t, a, n), i.state = e.memoizedState), typeof t.getDerivedStateFromProps == "function" || typeof i.getSnapshotBeforeUpdate == "function" || typeof i.UNSAFE_componentWillMount != "function" && typeof i.componentWillMount != "function" || (t = i.state, typeof i.componentWillMount == "function" && i.componentWillMount(), typeof i.UNSAFE_componentWillMount == "function" && i.UNSAFE_componentWillMount(), t !== i.state && xs.enqueueReplaceState(i, i.state, null), so(e, n, i, r), i.state = e.memoizedState), typeof i.componentDidMount == "function" && (e.flags |= 4194308);
	}
	function Es(e, t) {
		try {
			var n = "", r = t;
			do
				n += ce(r), r = r.return;
			while (r);
			var i = n;
		} catch (e) {
			i = "\nError generating stack: " + e.message + "\n" + e.stack;
		}
		return {
			value: e,
			source: t,
			stack: i,
			digest: null
		};
	}
	function Ds(e, t, n) {
		return {
			value: e,
			source: null,
			stack: n == null ? null : n,
			digest: t == null ? null : t
		};
	}
	function Os(e, t) {
		try {
			console.error(t.value);
		} catch (e) {
			setTimeout(function() {
				throw e;
			});
		}
	}
	var ks = typeof WeakMap == "function" ? WeakMap : Map;
	function As(e, t, n) {
		n = ro(-1, n), n.tag = 3, n.payload = { element: null };
		var r = t.value;
		return n.callback = function() {
			al || (al = !0, ol = r), Os(e, t);
		}, n;
	}
	function js(e, t, n) {
		n = ro(-1, n), n.tag = 3;
		var r = e.type.getDerivedStateFromError;
		if (typeof r == "function") {
			var i = t.value;
			n.payload = function() {
				return r(i);
			}, n.callback = function() {
				Os(e, t);
			};
		}
		var a = e.stateNode;
		return a !== null && typeof a.componentDidCatch == "function" && (n.callback = function() {
			Os(e, t), typeof r != "function" && (sl === null ? sl = /* @__PURE__ */ new Set([this]) : sl.add(this));
			var n = t.stack;
			this.componentDidCatch(t.value, { componentStack: n === null ? "" : n });
		}), n;
	}
	function Ms(e, t, n) {
		var r = e.pingCache;
		if (r === null) {
			r = e.pingCache = new ks();
			var i = /* @__PURE__ */ new Set();
			r.set(t, i);
		} else i = r.get(t), i === void 0 && (i = /* @__PURE__ */ new Set(), r.set(t, i));
		i.has(n) || (i.add(n), e = Hl.bind(null, e, t, n), t.then(e, e));
	}
	function Ns(e) {
		do {
			var t;
			if ((t = e.tag === 13) && (t = e.memoizedState, t = t === null || t.dehydrated !== null), t) return e;
			e = e.return;
		} while (e !== null);
		return null;
	}
	function Ps(e, t, n, r, i) {
		return e.mode & 1 ? (e.flags |= 65536, e.lanes = i, e) : (e === t ? e.flags |= 65536 : (e.flags |= 128, n.flags |= 131072, n.flags &= -52805, n.tag === 1 && (n.alternate === null ? n.tag = 17 : (t = ro(-1, 1), t.tag = 2, io(n, t, 1))), n.lanes |= 1), e);
	}
	var Fs = C.ReactCurrentOwner, Is = !1;
	function Ls(e, t, n, r) {
		t.child = e === null ? Ba(t, null, n, r) : G(t, e.child, n, r);
	}
	function Rs(e, t, n, r, i) {
		n = n.render;
		var a = t.ref;
		return Ja(t, i), r = Po(e, t, n, r, a, i), n = Fo(), e !== null && !Is ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, ic(e, t, i)) : (U && n && Sa(t), t.flags |= 1, Ls(e, t, r, i), t.child);
	}
	function zs(e, t, n, r, i) {
		if (e === null) {
			var a = n.type;
			return typeof a == "function" && !Xl(a) && a.defaultProps === void 0 && n.compare === null && n.defaultProps === void 0 ? (t.tag = 15, t.type = a, Bs(e, t, a, r, i)) : (e = $l(n.type, null, r, t, t.mode, i), e.ref = t.ref, e.return = t, t.child = e);
		}
		if (a = e.child, (e.lanes & i) === 0) {
			var o = a.memoizedProps;
			if (n = n.compare, n = n === null ? jr : n, n(o, r) && e.ref === t.ref) return ic(e, t, i);
		}
		return t.flags |= 1, e = Ql(a, r), e.ref = t.ref, e.return = t, t.child = e;
	}
	function Bs(e, t, n, r, i) {
		if (e !== null) {
			var a = e.memoizedProps;
			if (jr(a, r) && e.ref === t.ref) if (Is = !1, t.pendingProps = r = a, (e.lanes & i) !== 0) e.flags & 131072 && (Is = !0);
			else return t.lanes = e.lanes, ic(e, t, i);
		}
		return Us(e, t, n, r, i);
	}
	function Vs(e, t, n) {
		var r = t.pendingProps, i = r.children, a = e === null ? null : e.memoizedState;
		if (r.mode === "hidden") if (!(t.mode & 1)) t.memoizedState = {
			baseLanes: 0,
			cachePool: null,
			transitions: null
		}, H(Jc, qc), qc |= n;
		else {
			if (!(n & 1073741824)) return e = a === null ? n : a.baseLanes | n, t.lanes = t.childLanes = 1073741824, t.memoizedState = {
				baseLanes: e,
				cachePool: null,
				transitions: null
			}, t.updateQueue = null, H(Jc, qc), qc |= e, null;
			t.memoizedState = {
				baseLanes: 0,
				cachePool: null,
				transitions: null
			}, r = a === null ? n : a.baseLanes, H(Jc, qc), qc |= r;
		}
		else a === null ? r = n : (r = a.baseLanes | n, t.memoizedState = null), H(Jc, qc), qc |= r;
		return Ls(e, t, i, n), t.child;
	}
	function Hs(e, t) {
		var n = t.ref;
		(e === null && n !== null || e !== null && e.ref !== n) && (t.flags |= 512, t.flags |= 2097152);
	}
	function Us(e, t, n, r, i) {
		var a = $i(n) ? Zi : Yi.current;
		return a = Qi(t, a), Ja(t, i), n = Po(e, t, n, r, a, i), r = Fo(), e !== null && !Is ? (t.updateQueue = e.updateQueue, t.flags &= -2053, e.lanes &= ~i, ic(e, t, i)) : (U && r && Sa(t), t.flags |= 1, Ls(e, t, n, i), t.child);
	}
	function Ws(e, t, n, r, i) {
		if ($i(n)) {
			var a = !0;
			ra(t);
		} else a = !1;
		if (Ja(t, i), t.stateNode === null) rc(e, t), Cs(t, n, r), Ts(t, n, r, i), r = !0;
		else if (e === null) {
			var o = t.stateNode, s = t.memoizedProps;
			o.props = s;
			var c = o.context, l = n.contextType;
			typeof l == "object" && l ? l = Ya(l) : (l = $i(n) ? Zi : Yi.current, l = Qi(t, l));
			var u = n.getDerivedStateFromProps, d = typeof u == "function" || typeof o.getSnapshotBeforeUpdate == "function";
			d || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== r || c !== l) && ws(t, o, r, l), eo = !1;
			var f = t.memoizedState;
			o.state = f, so(t, r, o, i), c = t.memoizedState, s !== r || f !== c || Xi.current || eo ? (typeof u == "function" && (bs(t, n, u, r), c = t.memoizedState), (s = eo || Ss(t, n, s, r, f, c, l)) ? (d || typeof o.UNSAFE_componentWillMount != "function" && typeof o.componentWillMount != "function" || (typeof o.componentWillMount == "function" && o.componentWillMount(), typeof o.UNSAFE_componentWillMount == "function" && o.UNSAFE_componentWillMount()), typeof o.componentDidMount == "function" && (t.flags |= 4194308)) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), t.memoizedProps = r, t.memoizedState = c), o.props = r, o.state = c, o.context = l, r = s) : (typeof o.componentDidMount == "function" && (t.flags |= 4194308), r = !1);
		} else {
			o = t.stateNode, no(e, t), s = t.memoizedProps, l = t.type === t.elementType ? s : ys(t.type, s), o.props = l, d = t.pendingProps, f = o.context, c = n.contextType, typeof c == "object" && c ? c = Ya(c) : (c = $i(n) ? Zi : Yi.current, c = Qi(t, c));
			var p = n.getDerivedStateFromProps;
			(u = typeof p == "function" || typeof o.getSnapshotBeforeUpdate == "function") || typeof o.UNSAFE_componentWillReceiveProps != "function" && typeof o.componentWillReceiveProps != "function" || (s !== d || f !== c) && ws(t, o, r, c), eo = !1, f = t.memoizedState, o.state = f, so(t, r, o, i);
			var m = t.memoizedState;
			s !== d || f !== m || Xi.current || eo ? (typeof p == "function" && (bs(t, n, p, r), m = t.memoizedState), (l = eo || Ss(t, n, l, r, f, m, c) || !1) ? (u || typeof o.UNSAFE_componentWillUpdate != "function" && typeof o.componentWillUpdate != "function" || (typeof o.componentWillUpdate == "function" && o.componentWillUpdate(r, m, c), typeof o.UNSAFE_componentWillUpdate == "function" && o.UNSAFE_componentWillUpdate(r, m, c)), typeof o.componentDidUpdate == "function" && (t.flags |= 4), typeof o.getSnapshotBeforeUpdate == "function" && (t.flags |= 1024)) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), t.memoizedProps = r, t.memoizedState = m), o.props = r, o.state = m, o.context = c, r = l) : (typeof o.componentDidUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 4), typeof o.getSnapshotBeforeUpdate != "function" || s === e.memoizedProps && f === e.memoizedState || (t.flags |= 1024), r = !1);
		}
		return Gs(e, t, n, r, a, i);
	}
	function Gs(e, t, n, r, i, a) {
		Hs(e, t);
		var o = (t.flags & 128) != 0;
		if (!r && !o) return i && ia(t, n, !1), ic(e, t, a);
		r = t.stateNode, Fs.current = t;
		var s = o && typeof n.getDerivedStateFromError != "function" ? null : r.render();
		return t.flags |= 1, e !== null && o ? (t.child = G(t, e.child, null, a), t.child = G(t, null, s, a)) : Ls(e, t, s, a), t.memoizedState = r.state, i && ia(t, n, !0), t.child;
	}
	function Ks(e) {
		var t = e.stateNode;
		t.pendingContext ? ta(e, t.pendingContext, t.pendingContext !== t.context) : t.context && ta(e, t.context, !1), ho(e, t.containerInfo);
	}
	function qs(e, t, n, r, i) {
		return Na(), Pa(i), t.flags |= 256, Ls(e, t, n, r), t.child;
	}
	var Js = {
		dehydrated: null,
		treeContext: null,
		retryLane: 0
	};
	function Ys(e) {
		return {
			baseLanes: e,
			cachePool: null,
			transitions: null
		};
	}
	function Xs(e, t, n) {
		var r = t.pendingProps, i = yo.current, a = !1, o = (t.flags & 128) != 0, s;
		if ((s = o) || (s = e !== null && e.memoizedState === null ? !1 : (i & 2) != 0), s ? (a = !0, t.flags &= -129) : (e === null || e.memoizedState !== null) && (i |= 1), H(yo, i & 1), e === null) return ka(t), e = t.memoizedState, e !== null && (e = e.dehydrated, e !== null) ? (t.mode & 1 ? e.data === "$!" ? t.lanes = 8 : t.lanes = 1073741824 : t.lanes = 1, null) : (o = r.children, e = r.fallback, a ? (r = t.mode, a = t.child, o = {
			mode: "hidden",
			children: o
		}, !(r & 1) && a !== null ? (a.childLanes = 0, a.pendingProps = o) : a = tu(o, r, 0, null), e = eu(e, r, n, null), a.return = t, e.return = t, a.sibling = e, t.child = a, t.child.memoizedState = Ys(n), t.memoizedState = Js, e) : Zs(t, o));
		if (i = e.memoizedState, i !== null && (s = i.dehydrated, s !== null)) return $s(e, t, o, r, s, i, n);
		if (a) {
			a = r.fallback, o = t.mode, i = e.child, s = i.sibling;
			var c = {
				mode: "hidden",
				children: r.children
			};
			return !(o & 1) && t.child !== i ? (r = t.child, r.childLanes = 0, r.pendingProps = c, t.deletions = null) : (r = Ql(i, c), r.subtreeFlags = i.subtreeFlags & 14680064), s === null ? (a = eu(a, o, n, null), a.flags |= 2) : a = Ql(s, a), a.return = t, r.return = t, r.sibling = a, t.child = r, r = a, a = t.child, o = e.child.memoizedState, o = o === null ? Ys(n) : {
				baseLanes: o.baseLanes | n,
				cachePool: null,
				transitions: o.transitions
			}, a.memoizedState = o, a.childLanes = e.childLanes & ~n, t.memoizedState = Js, r;
		}
		return a = e.child, e = a.sibling, r = Ql(a, {
			mode: "visible",
			children: r.children
		}), !(t.mode & 1) && (r.lanes = n), r.return = t, r.sibling = null, e !== null && (n = t.deletions, n === null ? (t.deletions = [e], t.flags |= 16) : n.push(e)), t.child = r, t.memoizedState = null, r;
	}
	function Zs(e, t) {
		return t = tu({
			mode: "visible",
			children: t
		}, e.mode, 0, null), t.return = e, e.child = t;
	}
	function Qs(e, t, n, r) {
		return r !== null && Pa(r), G(t, e.child, null, n), e = Zs(t, t.pendingProps.children), e.flags |= 2, t.memoizedState = null, e;
	}
	function $s(e, t, n, i, a, o, s) {
		if (n) return t.flags & 256 ? (t.flags &= -257, i = Ds(Error(r(422))), Qs(e, t, s, i)) : t.memoizedState === null ? (o = i.fallback, a = t.mode, i = tu({
			mode: "visible",
			children: i.children
		}, a, 0, null), o = eu(o, a, s, null), o.flags |= 2, i.return = t, o.return = t, i.sibling = o, t.child = i, t.mode & 1 && G(t, e.child, null, s), t.child.memoizedState = Ys(s), t.memoizedState = Js, o) : (t.child = e.child, t.flags |= 128, null);
		if (!(t.mode & 1)) return Qs(e, t, s, null);
		if (a.data === "$!") {
			if (i = a.nextSibling && a.nextSibling.dataset, i) var c = i.dgst;
			return i = c, o = Error(r(419)), i = Ds(o, i, void 0), Qs(e, t, s, i);
		}
		if (c = (s & e.childLanes) !== 0, Is || c) {
			if (i = Wc, i !== null) {
				switch (s & -s) {
					case 4:
						a = 2;
						break;
					case 16:
						a = 8;
						break;
					case 64:
					case 128:
					case 256:
					case 512:
					case 1024:
					case 2048:
					case 4096:
					case 8192:
					case 16384:
					case 32768:
					case 65536:
					case 131072:
					case 262144:
					case 524288:
					case 1048576:
					case 2097152:
					case 4194304:
					case 8388608:
					case 16777216:
					case 33554432:
					case 67108864:
						a = 32;
						break;
					case 536870912:
						a = 268435456;
						break;
					default: a = 0;
				}
				a = (a & (i.suspendedLanes | s)) === 0 ? a : 0, a !== 0 && a !== o.retryLane && (o.retryLane = a, $a(e, a), _l(i, e, a, -1));
			}
			return jl(), i = Ds(Error(r(421))), Qs(e, t, s, i);
		}
		return a.data === "$?" ? (t.flags |= 128, t.child = e.child, t = Wl.bind(null, e), a._reactRetry = t, null) : (e = o.treeContext, Ta = Mi(a.nextSibling), wa = t, U = !0, Ea = null, e !== null && (ha[ga++] = va, ha[ga++] = ya, ha[ga++] = _a, va = e.id, ya = e.overflow, _a = t), t = Zs(t, i.children), t.flags |= 4096, t);
	}
	function ec(e, t, n) {
		e.lanes |= t;
		var r = e.alternate;
		r !== null && (r.lanes |= t), qa(e.return, t, n);
	}
	function tc(e, t, n, r, i) {
		var a = e.memoizedState;
		a === null ? e.memoizedState = {
			isBackwards: t,
			rendering: null,
			renderingStartTime: 0,
			last: r,
			tail: n,
			tailMode: i
		} : (a.isBackwards = t, a.rendering = null, a.renderingStartTime = 0, a.last = r, a.tail = n, a.tailMode = i);
	}
	function nc(e, t, n) {
		var r = t.pendingProps, i = r.revealOrder, a = r.tail;
		if (Ls(e, t, r.children, n), r = yo.current, r & 2) r = r & 1 | 2, t.flags |= 128;
		else {
			if (e !== null && e.flags & 128) a: for (e = t.child; e !== null;) {
				if (e.tag === 13) e.memoizedState !== null && ec(e, n, t);
				else if (e.tag === 19) ec(e, n, t);
				else if (e.child !== null) {
					e.child.return = e, e = e.child;
					continue;
				}
				if (e === t) break a;
				for (; e.sibling === null;) {
					if (e.return === null || e.return === t) break a;
					e = e.return;
				}
				e.sibling.return = e.return, e = e.sibling;
			}
			r &= 1;
		}
		if (H(yo, r), !(t.mode & 1)) t.memoizedState = null;
		else switch (i) {
			case "forwards":
				for (n = t.child, i = null; n !== null;) e = n.alternate, e !== null && bo(e) === null && (i = n), n = n.sibling;
				n = i, n === null ? (i = t.child, t.child = null) : (i = n.sibling, n.sibling = null), tc(t, !1, i, n, a);
				break;
			case "backwards":
				for (n = null, i = t.child, t.child = null; i !== null;) {
					if (e = i.alternate, e !== null && bo(e) === null) {
						t.child = i;
						break;
					}
					e = i.sibling, i.sibling = n, n = i, i = e;
				}
				tc(t, !0, n, null, a);
				break;
			case "together":
				tc(t, !1, null, null, void 0);
				break;
			default: t.memoizedState = null;
		}
		return t.child;
	}
	function rc(e, t) {
		!(t.mode & 1) && e !== null && (e.alternate = null, t.alternate = null, t.flags |= 2);
	}
	function ic(e, t, n) {
		if (e !== null && (t.dependencies = e.dependencies), Zc |= t.lanes, (n & t.childLanes) === 0) return null;
		if (e !== null && t.child !== e.child) throw Error(r(153));
		if (t.child !== null) {
			for (e = t.child, n = Ql(e, e.pendingProps), t.child = n, n.return = t; e.sibling !== null;) e = e.sibling, n = n.sibling = Ql(e, e.pendingProps), n.return = t;
			n.sibling = null;
		}
		return t.child;
	}
	function ac(e, t, n) {
		switch (t.tag) {
			case 3:
				Ks(t), Na();
				break;
			case 5:
				_o(t);
				break;
			case 1:
				$i(t.type) && ra(t);
				break;
			case 4:
				ho(t, t.stateNode.containerInfo);
				break;
			case 10:
				var r = t.type._context, i = t.memoizedProps.value;
				H(Va, r._currentValue), r._currentValue = i;
				break;
			case 13:
				if (r = t.memoizedState, r !== null) return r.dehydrated === null ? (n & t.child.childLanes) === 0 ? (H(yo, yo.current & 1), e = ic(e, t, n), e === null ? null : e.sibling) : Xs(e, t, n) : (H(yo, yo.current & 1), t.flags |= 128, null);
				H(yo, yo.current & 1);
				break;
			case 19:
				if (r = (n & t.childLanes) !== 0, e.flags & 128) {
					if (r) return nc(e, t, n);
					t.flags |= 128;
				}
				if (i = t.memoizedState, i !== null && (i.rendering = null, i.tail = null, i.lastEffect = null), H(yo, yo.current), r) break;
				return null;
			case 22:
			case 23: return t.lanes = 0, Vs(e, t, n);
		}
		return ic(e, t, n);
	}
	var oc = function(e, t) {
		for (var n = t.child; n !== null;) {
			if (n.tag === 5 || n.tag === 6) e.appendChild(n.stateNode);
			else if (n.tag !== 4 && n.child !== null) {
				n.child.return = n, n = n.child;
				continue;
			}
			if (n === t) break;
			for (; n.sibling === null;) {
				if (n.return === null || n.return === t) return;
				n = n.return;
			}
			n.sibling.return = n.return, n = n.sibling;
		}
	}, sc = function(e, t, n, r) {
		var i = e.memoizedProps;
		if (i !== r) {
			e = t.stateNode, mo(uo.current);
			var o = null;
			switch (n) {
				case "input":
					i = _e(e, i), r = _e(e, r), o = [];
					break;
				case "select":
					i = F({}, i, { value: void 0 }), r = F({}, r, { value: void 0 }), o = [];
					break;
				case "textarea":
					i = Te(e, i), r = Te(e, r), o = [];
					break;
				default: typeof i.onClick != "function" && typeof r.onClick == "function" && (e.onclick = Si);
			}
			ze(n, r);
			var s;
			for (u in n = null, i) if (!r.hasOwnProperty(u) && i.hasOwnProperty(u) && i[u] != null) if (u === "style") {
				var c = i[u];
				for (s in c) c.hasOwnProperty(s) && (n || (n = {}), n[s] = "");
			} else u !== "dangerouslySetInnerHTML" && u !== "children" && u !== "suppressContentEditableWarning" && u !== "suppressHydrationWarning" && u !== "autoFocus" && (a.hasOwnProperty(u) ? o || (o = []) : (o = o || []).push(u, null));
			for (u in r) {
				var l = r[u];
				if (c = i == null ? void 0 : i[u], r.hasOwnProperty(u) && l !== c && (l != null || c != null)) if (u === "style") if (c) {
					for (s in c) !c.hasOwnProperty(s) || l && l.hasOwnProperty(s) || (n || (n = {}), n[s] = "");
					for (s in l) l.hasOwnProperty(s) && c[s] !== l[s] && (n || (n = {}), n[s] = l[s]);
				} else n || (o || (o = []), o.push(u, n)), n = l;
				else u === "dangerouslySetInnerHTML" ? (l = l ? l.__html : void 0, c = c ? c.__html : void 0, l != null && c !== l && (o = o || []).push(u, l)) : u === "children" ? typeof l != "string" && typeof l != "number" || (o = o || []).push(u, "" + l) : u !== "suppressContentEditableWarning" && u !== "suppressHydrationWarning" && (a.hasOwnProperty(u) ? (l != null && u === "onScroll" && ci("scroll", e), o || c === l || (o = [])) : (o = o || []).push(u, l));
			}
			n && (o = o || []).push("style", n);
			var u = o;
			(t.updateQueue = u) && (t.flags |= 4);
		}
	}, cc = function(e, t, n, r) {
		n !== r && (t.flags |= 4);
	};
	function lc(e, t) {
		if (!U) switch (e.tailMode) {
			case "hidden":
				t = e.tail;
				for (var n = null; t !== null;) t.alternate !== null && (n = t), t = t.sibling;
				n === null ? e.tail = null : n.sibling = null;
				break;
			case "collapsed":
				n = e.tail;
				for (var r = null; n !== null;) n.alternate !== null && (r = n), n = n.sibling;
				r === null ? t || e.tail === null ? e.tail = null : e.tail.sibling = null : r.sibling = null;
		}
	}
	function uc(e) {
		var t = e.alternate !== null && e.alternate.child === e.child, n = 0, r = 0;
		if (t) for (var i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags & 14680064, r |= i.flags & 14680064, i.return = e, i = i.sibling;
		else for (i = e.child; i !== null;) n |= i.lanes | i.childLanes, r |= i.subtreeFlags, r |= i.flags, i.return = e, i = i.sibling;
		return e.subtreeFlags |= r, e.childLanes = n, t;
	}
	function dc(e, t, n) {
		var i = t.pendingProps;
		switch (Ca(t), t.tag) {
			case 2:
			case 16:
			case 15:
			case 0:
			case 11:
			case 7:
			case 8:
			case 12:
			case 9:
			case 14: return uc(t), null;
			case 1: return $i(t.type) && ea(), uc(t), null;
			case 3: return i = t.stateNode, go(), V(Xi), V(Yi), So(), i.pendingContext && (i.context = i.pendingContext, i.pendingContext = null), (e === null || e.child === null) && (ja(t) ? t.flags |= 4 : e === null || e.memoizedState.isDehydrated && !(t.flags & 256) || (t.flags |= 1024, Ea !== null && (xl(Ea), Ea = null))), uc(t), null;
			case 5:
				vo(t);
				var o = mo(po.current);
				if (n = t.type, e !== null && t.stateNode != null) sc(e, t, n, i, o), e.ref !== t.ref && (t.flags |= 512, t.flags |= 2097152);
				else {
					if (!i) {
						if (t.stateNode === null) throw Error(r(166));
						return uc(t), null;
					}
					if (e = mo(uo.current), ja(t)) {
						i = t.stateNode, n = t.type;
						var s = t.memoizedProps;
						switch (i[Fi] = t, i[Ii] = s, e = (t.mode & 1) != 0, n) {
							case "dialog":
								ci("cancel", i), ci("close", i);
								break;
							case "iframe":
							case "object":
							case "embed":
								ci("load", i);
								break;
							case "video":
							case "audio":
								for (o = 0; o < ii.length; o++) ci(ii[o], i);
								break;
							case "source":
								ci("error", i);
								break;
							case "img":
							case "image":
							case "link":
								ci("error", i), ci("load", i);
								break;
							case "details":
								ci("toggle", i);
								break;
							case "input":
								ve(i, s), ci("invalid", i);
								break;
							case "select":
								i._wrapperState = { wasMultiple: !!s.multiple }, ci("invalid", i);
								break;
							case "textarea": Ee(i, s), ci("invalid", i);
						}
						for (var c in ze(n, s), o = null, s) if (s.hasOwnProperty(c)) {
							var l = s[c];
							c === "children" ? typeof l == "string" ? i.textContent !== l && (!0 !== s.suppressHydrationWarning && xi(i.textContent, l, e), o = ["children", l]) : typeof l == "number" && i.textContent !== "" + l && (!0 !== s.suppressHydrationWarning && xi(i.textContent, l, e), o = ["children", "" + l]) : a.hasOwnProperty(c) && l != null && c === "onScroll" && ci("scroll", i);
						}
						switch (n) {
							case "input":
								me(i), xe(i, s, !0);
								break;
							case "textarea":
								me(i), Oe(i);
								break;
							case "select":
							case "option": break;
							default: typeof s.onClick == "function" && (i.onclick = Si);
						}
						i = o, t.updateQueue = i, i !== null && (t.flags |= 4);
					} else {
						c = o.nodeType === 9 ? o : o.ownerDocument, e === "http://www.w3.org/1999/xhtml" && (e = ke(n)), e === "http://www.w3.org/1999/xhtml" ? n === "script" ? (e = c.createElement("div"), e.innerHTML = "<script><\/script>", e = e.removeChild(e.firstChild)) : typeof i.is == "string" ? e = c.createElement(n, { is: i.is }) : (e = c.createElement(n), n === "select" && (c = e, i.multiple ? c.multiple = !0 : i.size && (c.size = i.size))) : e = c.createElementNS(e, n), e[Fi] = t, e[Ii] = i, oc(e, t, !1, !1), t.stateNode = e;
						a: {
							switch (c = Be(n, i), n) {
								case "dialog":
									ci("cancel", e), ci("close", e), o = i;
									break;
								case "iframe":
								case "object":
								case "embed":
									ci("load", e), o = i;
									break;
								case "video":
								case "audio":
									for (o = 0; o < ii.length; o++) ci(ii[o], e);
									o = i;
									break;
								case "source":
									ci("error", e), o = i;
									break;
								case "img":
								case "image":
								case "link":
									ci("error", e), ci("load", e), o = i;
									break;
								case "details":
									ci("toggle", e), o = i;
									break;
								case "input":
									ve(e, i), o = _e(e, i), ci("invalid", e);
									break;
								case "option":
									o = i;
									break;
								case "select":
									e._wrapperState = { wasMultiple: !!i.multiple }, o = F({}, i, { value: void 0 }), ci("invalid", e);
									break;
								case "textarea":
									Ee(e, i), o = Te(e, i), ci("invalid", e);
									break;
								default: o = i;
							}
							for (s in ze(n, o), l = o, l) if (l.hasOwnProperty(s)) {
								var u = l[s];
								s === "style" ? Le(e, u) : s === "dangerouslySetInnerHTML" ? (u = u ? u.__html : void 0, u != null && Me(e, u)) : s === "children" ? typeof u == "string" ? (n !== "textarea" || u !== "") && Ne(e, u) : typeof u == "number" && Ne(e, "" + u) : s !== "suppressContentEditableWarning" && s !== "suppressHydrationWarning" && s !== "autoFocus" && (a.hasOwnProperty(s) ? u != null && s === "onScroll" && ci("scroll", e) : u != null && S(e, s, u, c));
							}
							switch (n) {
								case "input":
									me(e), xe(e, i, !1);
									break;
								case "textarea":
									me(e), Oe(e);
									break;
								case "option":
									i.value != null && e.setAttribute("value", "" + de(i.value));
									break;
								case "select":
									e.multiple = !!i.multiple, s = i.value, s == null ? i.defaultValue != null && we(e, !!i.multiple, i.defaultValue, !0) : we(e, !!i.multiple, s, !1);
									break;
								default: typeof o.onClick == "function" && (e.onclick = Si);
							}
							switch (n) {
								case "button":
								case "input":
								case "select":
								case "textarea":
									i = !!i.autoFocus;
									break a;
								case "img":
									i = !0;
									break a;
								default: i = !1;
							}
						}
						i && (t.flags |= 4);
					}
					t.ref !== null && (t.flags |= 512, t.flags |= 2097152);
				}
				return uc(t), null;
			case 6:
				if (e && t.stateNode != null) cc(e, t, e.memoizedProps, i);
				else {
					if (typeof i != "string" && t.stateNode === null) throw Error(r(166));
					if (n = mo(po.current), mo(uo.current), ja(t)) {
						if (i = t.stateNode, n = t.memoizedProps, i[Fi] = t, (s = i.nodeValue !== n) && (e = wa, e !== null)) switch (e.tag) {
							case 3:
								xi(i.nodeValue, n, (e.mode & 1) != 0);
								break;
							case 5: !0 !== e.memoizedProps.suppressHydrationWarning && xi(i.nodeValue, n, (e.mode & 1) != 0);
						}
						s && (t.flags |= 4);
					} else i = (n.nodeType === 9 ? n : n.ownerDocument).createTextNode(i), i[Fi] = t, t.stateNode = i;
				}
				return uc(t), null;
			case 13:
				if (V(yo), i = t.memoizedState, e === null || e.memoizedState !== null && e.memoizedState.dehydrated !== null) {
					if (U && Ta !== null && t.mode & 1 && !(t.flags & 128)) Ma(), Na(), t.flags |= 98560, s = !1;
					else if (s = ja(t), i !== null && i.dehydrated !== null) {
						if (e === null) {
							if (!s) throw Error(r(318));
							if (s = t.memoizedState, s = s === null ? null : s.dehydrated, !s) throw Error(r(317));
							s[Fi] = t;
						} else Na(), !(t.flags & 128) && (t.memoizedState = null), t.flags |= 4;
						uc(t), s = !1;
					} else Ea !== null && (xl(Ea), Ea = null), s = !0;
					if (!s) return t.flags & 65536 ? t : null;
				}
				return t.flags & 128 ? (t.lanes = n, t) : (i = i !== null, i !== (e !== null && e.memoizedState !== null) && i && (t.child.flags |= 8192, t.mode & 1 && (e === null || yo.current & 1 ? Yc === 0 && (Yc = 3) : jl())), t.updateQueue !== null && (t.flags |= 4), uc(t), null);
			case 4: return go(), e === null && di(t.stateNode.containerInfo), uc(t), null;
			case 10: return Ka(t.type._context), uc(t), null;
			case 17: return $i(t.type) && ea(), uc(t), null;
			case 19:
				if (V(yo), s = t.memoizedState, s === null) return uc(t), null;
				if (i = (t.flags & 128) != 0, c = s.rendering, c === null) if (i) lc(s, !1);
				else {
					if (Yc !== 0 || e !== null && e.flags & 128) for (e = t.child; e !== null;) {
						if (c = bo(e), c !== null) {
							for (t.flags |= 128, lc(s, !1), i = c.updateQueue, i !== null && (t.updateQueue = i, t.flags |= 4), t.subtreeFlags = 0, i = n, n = t.child; n !== null;) s = n, e = i, s.flags &= 14680066, c = s.alternate, c === null ? (s.childLanes = 0, s.lanes = e, s.child = null, s.subtreeFlags = 0, s.memoizedProps = null, s.memoizedState = null, s.updateQueue = null, s.dependencies = null, s.stateNode = null) : (s.childLanes = c.childLanes, s.lanes = c.lanes, s.child = c.child, s.subtreeFlags = 0, s.deletions = null, s.memoizedProps = c.memoizedProps, s.memoizedState = c.memoizedState, s.updateQueue = c.updateQueue, s.type = c.type, e = c.dependencies, s.dependencies = e === null ? null : {
								lanes: e.lanes,
								firstContext: e.firstContext
							}), n = n.sibling;
							return H(yo, yo.current & 1 | 2), t.child;
						}
						e = e.sibling;
					}
					s.tail !== null && bt() > rl && (t.flags |= 128, i = !0, lc(s, !1), t.lanes = 4194304);
				}
				else {
					if (!i) if (e = bo(c), e !== null) {
						if (t.flags |= 128, i = !0, n = e.updateQueue, n !== null && (t.updateQueue = n, t.flags |= 4), lc(s, !0), s.tail === null && s.tailMode === "hidden" && !c.alternate && !U) return uc(t), null;
					} else 2 * bt() - s.renderingStartTime > rl && n !== 1073741824 && (t.flags |= 128, i = !0, lc(s, !1), t.lanes = 4194304);
					s.isBackwards ? (c.sibling = t.child, t.child = c) : (n = s.last, n === null ? t.child = c : n.sibling = c, s.last = c);
				}
				return s.tail === null ? (uc(t), null) : (t = s.tail, s.rendering = t, s.tail = t.sibling, s.renderingStartTime = bt(), t.sibling = null, n = yo.current, H(yo, i ? n & 1 | 2 : n & 1), t);
			case 22:
			case 23: return Dl(), i = t.memoizedState !== null, e !== null && e.memoizedState !== null !== i && (t.flags |= 8192), i && t.mode & 1 ? qc & 1073741824 && (uc(t), t.subtreeFlags & 6 && (t.flags |= 8192)) : uc(t), null;
			case 24: return null;
			case 25: return null;
		}
		throw Error(r(156, t.tag));
	}
	function fc(e, t) {
		switch (Ca(t), t.tag) {
			case 1: return $i(t.type) && ea(), e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 3: return go(), V(Xi), V(Yi), So(), e = t.flags, e & 65536 && !(e & 128) ? (t.flags = e & -65537 | 128, t) : null;
			case 5: return vo(t), null;
			case 13:
				if (V(yo), e = t.memoizedState, e !== null && e.dehydrated !== null) {
					if (t.alternate === null) throw Error(r(340));
					Na();
				}
				return e = t.flags, e & 65536 ? (t.flags = e & -65537 | 128, t) : null;
			case 19: return V(yo), null;
			case 4: return go(), null;
			case 10: return Ka(t.type._context), null;
			case 22:
			case 23: return Dl(), null;
			case 24: return null;
			default: return null;
		}
	}
	var pc = !1, mc = !1, hc = typeof WeakSet == "function" ? WeakSet : Set, J = null;
	function gc(e, t) {
		var n = e.ref;
		if (n !== null) if (typeof n == "function") try {
			n(null);
		} catch (n) {
			Vl(e, t, n);
		}
		else n.current = null;
	}
	function _c(e, t, n) {
		try {
			n();
		} catch (n) {
			Vl(e, t, n);
		}
	}
	var vc = !1;
	function yc(e, t) {
		if (Ci = _n, e = Fr(), Ir(e)) {
			if ("selectionStart" in e) var n = {
				start: e.selectionStart,
				end: e.selectionEnd
			};
			else a: {
				n = (n = e.ownerDocument) && n.defaultView || window;
				var i = n.getSelection && n.getSelection();
				if (i && i.rangeCount !== 0) {
					n = i.anchorNode;
					var a = i.anchorOffset, o = i.focusNode;
					i = i.focusOffset;
					try {
						n.nodeType, o.nodeType;
					} catch (e) {
						n = null;
						break a;
					}
					var s = 0, c = -1, l = -1, u = 0, d = 0, f = e, p = null;
					b: for (;;) {
						for (var m; f !== n || a !== 0 && f.nodeType !== 3 || (c = s + a), f !== o || i !== 0 && f.nodeType !== 3 || (l = s + i), f.nodeType === 3 && (s += f.nodeValue.length), (m = f.firstChild) !== null;) p = f, f = m;
						for (;;) {
							if (f === e) break b;
							if (p === n && ++u === a && (c = s), p === o && ++d === i && (l = s), (m = f.nextSibling) !== null) break;
							f = p, p = f.parentNode;
						}
						f = m;
					}
					n = c === -1 || l === -1 ? null : {
						start: c,
						end: l
					};
				} else n = null;
			}
			n = n || {
				start: 0,
				end: 0
			};
		} else n = null;
		for (wi = {
			focusedElem: e,
			selectionRange: n
		}, _n = !1, J = t; J !== null;) if (t = J, e = t.child, t.subtreeFlags & 1028 && e !== null) e.return = t, J = e;
		else for (; J !== null;) {
			t = J;
			try {
				var h = t.alternate;
				if (t.flags & 1024) switch (t.tag) {
					case 0:
					case 11:
					case 15: break;
					case 1:
						if (h !== null) {
							var g = h.memoizedProps, _ = h.memoizedState, v = t.stateNode;
							v.__reactInternalSnapshotBeforeUpdate = v.getSnapshotBeforeUpdate(t.elementType === t.type ? g : ys(t.type, g), _);
						}
						break;
					case 3:
						var y = t.stateNode.containerInfo;
						y.nodeType === 1 ? y.textContent = "" : y.nodeType === 9 && y.documentElement && y.removeChild(y.documentElement);
						break;
					case 5:
					case 6:
					case 4:
					case 17: break;
					default: throw Error(r(163));
				}
			} catch (e) {
				Vl(t, t.return, e);
			}
			if (e = t.sibling, e !== null) {
				e.return = t.return, J = e;
				break;
			}
			J = t.return;
		}
		return h = vc, vc = !1, h;
	}
	function bc(e, t, n) {
		var r = t.updateQueue;
		if (r = r === null ? null : r.lastEffect, r !== null) {
			var i = r = r.next;
			do {
				if ((i.tag & e) === e) {
					var a = i.destroy;
					i.destroy = void 0, a !== void 0 && _c(t, n, a);
				}
				i = i.next;
			} while (i !== r);
		}
	}
	function xc(e, t) {
		if (t = t.updateQueue, t = t === null ? null : t.lastEffect, t !== null) {
			var n = t = t.next;
			do {
				if ((n.tag & e) === e) {
					var r = n.create;
					n.destroy = r();
				}
				n = n.next;
			} while (n !== t);
		}
	}
	function Sc(e) {
		var t = e.ref;
		if (t !== null) {
			var n = e.stateNode;
			switch (e.tag) {
				case 5:
					e = n;
					break;
				default: e = n;
			}
			typeof t == "function" ? t(e) : t.current = e;
		}
	}
	function Cc(e) {
		var t = e.alternate;
		t !== null && (e.alternate = null, Cc(t)), e.child = null, e.deletions = null, e.sibling = null, e.tag === 5 && (t = e.stateNode, t !== null && (delete t[Fi], delete t[Ii], delete t[Ri], delete t[zi], delete t[Bi])), e.stateNode = null, e.return = null, e.dependencies = null, e.memoizedProps = null, e.memoizedState = null, e.pendingProps = null, e.stateNode = null, e.updateQueue = null;
	}
	function wc(e) {
		return e.tag === 5 || e.tag === 3 || e.tag === 4;
	}
	function Tc(e) {
		a: for (;;) {
			for (; e.sibling === null;) {
				if (e.return === null || wc(e.return)) return null;
				e = e.return;
			}
			for (e.sibling.return = e.return, e = e.sibling; e.tag !== 5 && e.tag !== 6 && e.tag !== 18;) {
				if (e.flags & 2 || e.child === null || e.tag === 4) continue a;
				e.child.return = e, e = e.child;
			}
			if (!(e.flags & 2)) return e.stateNode;
		}
	}
	function Ec(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.nodeType === 8 ? n.parentNode.insertBefore(e, t) : n.insertBefore(e, t) : (n.nodeType === 8 ? (t = n.parentNode, t.insertBefore(e, n)) : (t = n, t.appendChild(e)), n = n._reactRootContainer, n != null || t.onclick !== null || (t.onclick = Si));
		else if (r !== 4 && (e = e.child, e !== null)) for (Ec(e, t, n), e = e.sibling; e !== null;) Ec(e, t, n), e = e.sibling;
	}
	function Dc(e, t, n) {
		var r = e.tag;
		if (r === 5 || r === 6) e = e.stateNode, t ? n.insertBefore(e, t) : n.appendChild(e);
		else if (r !== 4 && (e = e.child, e !== null)) for (Dc(e, t, n), e = e.sibling; e !== null;) Dc(e, t, n), e = e.sibling;
	}
	var Oc = null, Y = !1;
	function kc(e, t, n) {
		for (n = n.child; n !== null;) Ac(e, t, n), n = n.sibling;
	}
	function Ac(e, t, n) {
		if (Ot && typeof Ot.onCommitFiberUnmount == "function") try {
			Ot.onCommitFiberUnmount(Dt, n);
		} catch (e) {}
		switch (n.tag) {
			case 5: mc || gc(n, t);
			case 6:
				var r = Oc, i = Y;
				Oc = null, kc(e, t, n), Oc = r, Y = i, Oc !== null && (Y ? (e = Oc, n = n.stateNode, e.nodeType === 8 ? e.parentNode.removeChild(n) : e.removeChild(n)) : Oc.removeChild(n.stateNode));
				break;
			case 18:
				Oc !== null && (Y ? (e = Oc, n = n.stateNode, e.nodeType === 8 ? ji(e.parentNode, n) : e.nodeType === 1 && ji(e, n), hn(e)) : ji(Oc, n.stateNode));
				break;
			case 4:
				r = Oc, i = Y, Oc = n.stateNode.containerInfo, Y = !0, kc(e, t, n), Oc = r, Y = i;
				break;
			case 0:
			case 11:
			case 14:
			case 15:
				if (!mc && (r = n.updateQueue, r !== null && (r = r.lastEffect, r !== null))) {
					i = r = r.next;
					do {
						var a = i, o = a.destroy;
						a = a.tag, o !== void 0 && (a & 2 || a & 4) && _c(n, t, o), i = i.next;
					} while (i !== r);
				}
				kc(e, t, n);
				break;
			case 1:
				if (!mc && (gc(n, t), r = n.stateNode, typeof r.componentWillUnmount == "function")) try {
					r.props = n.memoizedProps, r.state = n.memoizedState, r.componentWillUnmount();
				} catch (e) {
					Vl(n, t, e);
				}
				kc(e, t, n);
				break;
			case 21:
				kc(e, t, n);
				break;
			case 22:
				n.mode & 1 ? (mc = (r = mc) || n.memoizedState !== null, kc(e, t, n), mc = r) : kc(e, t, n);
				break;
			default: kc(e, t, n);
		}
	}
	function jc(e) {
		var t = e.updateQueue;
		if (t !== null) {
			e.updateQueue = null;
			var n = e.stateNode;
			n === null && (n = e.stateNode = new hc()), t.forEach(function(t) {
				var r = Gl.bind(null, e, t);
				n.has(t) || (n.add(t), t.then(r, r));
			});
		}
	}
	function Mc(e, t) {
		var n = t.deletions;
		if (n !== null) for (var i = 0; i < n.length; i++) {
			var a = n[i];
			try {
				var o = e, s = t, c = s;
				a: for (; c !== null;) {
					switch (c.tag) {
						case 5:
							Oc = c.stateNode, Y = !1;
							break a;
						case 3:
							Oc = c.stateNode.containerInfo, Y = !0;
							break a;
						case 4:
							Oc = c.stateNode.containerInfo, Y = !0;
							break a;
					}
					c = c.return;
				}
				if (Oc === null) throw Error(r(160));
				Ac(o, s, a), Oc = null, Y = !1;
				var l = a.alternate;
				l !== null && (l.return = null), a.return = null;
			} catch (e) {
				Vl(a, t, e);
			}
		}
		if (t.subtreeFlags & 12854) for (t = t.child; t !== null;) Nc(t, e), t = t.sibling;
	}
	function Nc(e, t) {
		var n = e.alternate, i = e.flags;
		switch (e.tag) {
			case 0:
			case 11:
			case 14:
			case 15:
				if (Mc(t, e), Pc(e), i & 4) {
					try {
						bc(3, e, e.return), xc(3, e);
					} catch (t) {
						Vl(e, e.return, t);
					}
					try {
						bc(5, e, e.return);
					} catch (t) {
						Vl(e, e.return, t);
					}
				}
				break;
			case 1:
				Mc(t, e), Pc(e), i & 512 && n !== null && gc(n, n.return);
				break;
			case 5:
				if (Mc(t, e), Pc(e), i & 512 && n !== null && gc(n, n.return), e.flags & 32) {
					var a = e.stateNode;
					try {
						Ne(a, "");
					} catch (t) {
						Vl(e, e.return, t);
					}
				}
				if (i & 4 && (a = e.stateNode, a != null)) {
					var o = e.memoizedProps, s = n === null ? o : n.memoizedProps, c = e.type, l = e.updateQueue;
					if (e.updateQueue = null, l !== null) try {
						c === "input" && o.type === "radio" && o.name != null && ye(a, o), Be(c, s);
						var u = Be(c, o);
						for (s = 0; s < l.length; s += 2) {
							var d = l[s], f = l[s + 1];
							d === "style" ? Le(a, f) : d === "dangerouslySetInnerHTML" ? Me(a, f) : d === "children" ? Ne(a, f) : S(a, d, f, u);
						}
						switch (c) {
							case "input":
								be(a, o);
								break;
							case "textarea":
								De(a, o);
								break;
							case "select":
								var p = a._wrapperState.wasMultiple;
								a._wrapperState.wasMultiple = !!o.multiple;
								var m = o.value;
								m == null ? p !== !!o.multiple && (o.defaultValue == null ? we(a, !!o.multiple, o.multiple ? [] : "", !1) : we(a, !!o.multiple, o.defaultValue, !0)) : we(a, !!o.multiple, m, !1);
						}
						a[Ii] = o;
					} catch (t) {
						Vl(e, e.return, t);
					}
				}
				break;
			case 6:
				if (Mc(t, e), Pc(e), i & 4) {
					if (e.stateNode === null) throw Error(r(162));
					a = e.stateNode, o = e.memoizedProps;
					try {
						a.nodeValue = o;
					} catch (t) {
						Vl(e, e.return, t);
					}
				}
				break;
			case 3:
				if (Mc(t, e), Pc(e), i & 4 && n !== null && n.memoizedState.isDehydrated) try {
					hn(t.containerInfo);
				} catch (t) {
					Vl(e, e.return, t);
				}
				break;
			case 4:
				Mc(t, e), Pc(e);
				break;
			case 13:
				Mc(t, e), Pc(e), a = e.child, a.flags & 8192 && (o = a.memoizedState !== null, a.stateNode.isHidden = o, !o || a.alternate !== null && a.alternate.memoizedState !== null || (nl = bt())), i & 4 && jc(e);
				break;
			case 22:
				if (d = n !== null && n.memoizedState !== null, e.mode & 1 ? (mc = (u = mc) || d, Mc(t, e), mc = u) : Mc(t, e), Pc(e), i & 8192) {
					if (u = e.memoizedState !== null, (e.stateNode.isHidden = u) && !d && e.mode & 1) for (J = e, d = e.child; d !== null;) {
						for (f = J = d; J !== null;) {
							switch (p = J, m = p.child, p.tag) {
								case 0:
								case 11:
								case 14:
								case 15:
									bc(4, p, p.return);
									break;
								case 1:
									gc(p, p.return);
									var h = p.stateNode;
									if (typeof h.componentWillUnmount == "function") {
										i = p, n = p.return;
										try {
											t = i, h.props = t.memoizedProps, h.state = t.memoizedState, h.componentWillUnmount();
										} catch (e) {
											Vl(i, n, e);
										}
									}
									break;
								case 5:
									gc(p, p.return);
									break;
								case 22: if (p.memoizedState !== null) {
									Rc(f);
									continue;
								}
							}
							m === null ? Rc(f) : (m.return = p, J = m);
						}
						d = d.sibling;
					}
					a: for (d = null, f = e;;) {
						if (f.tag === 5) {
							if (d === null) {
								d = f;
								try {
									a = f.stateNode, u ? (o = a.style, typeof o.setProperty == "function" ? o.setProperty("display", "none", "important") : o.display = "none") : (c = f.stateNode, l = f.memoizedProps.style, s = l != null && l.hasOwnProperty("display") ? l.display : null, c.style.display = Ie("display", s));
								} catch (t) {
									Vl(e, e.return, t);
								}
							}
						} else if (f.tag === 6) {
							if (d === null) try {
								f.stateNode.nodeValue = u ? "" : f.memoizedProps;
							} catch (t) {
								Vl(e, e.return, t);
							}
						} else if ((f.tag !== 22 && f.tag !== 23 || f.memoizedState === null || f === e) && f.child !== null) {
							f.child.return = f, f = f.child;
							continue;
						}
						if (f === e) break a;
						for (; f.sibling === null;) {
							if (f.return === null || f.return === e) break a;
							d === f && (d = null), f = f.return;
						}
						d === f && (d = null), f.sibling.return = f.return, f = f.sibling;
					}
				}
				break;
			case 19:
				Mc(t, e), Pc(e), i & 4 && jc(e);
				break;
			case 21: break;
			default: Mc(t, e), Pc(e);
		}
	}
	function Pc(e) {
		var t = e.flags;
		if (t & 2) {
			try {
				a: {
					for (var n = e.return; n !== null;) {
						if (wc(n)) {
							var i = n;
							break a;
						}
						n = n.return;
					}
					throw Error(r(160));
				}
				switch (i.tag) {
					case 5:
						var a = i.stateNode;
						i.flags & 32 && (Ne(a, ""), i.flags &= -33), Dc(e, Tc(e), a);
						break;
					case 3:
					case 4:
						var o = i.stateNode.containerInfo;
						Ec(e, Tc(e), o);
						break;
					default: throw Error(r(161));
				}
			} catch (t) {
				Vl(e, e.return, t);
			}
			e.flags &= -3;
		}
		t & 4096 && (e.flags &= -4097);
	}
	function Fc(e, t, n) {
		J = e, Ic(e, t, n);
	}
	function Ic(e, t, n) {
		for (var r = (e.mode & 1) != 0; J !== null;) {
			var i = J, a = i.child;
			if (i.tag === 22 && r) {
				var o = i.memoizedState !== null || pc;
				if (!o) {
					var s = i.alternate, c = s !== null && s.memoizedState !== null || mc;
					s = pc;
					var l = mc;
					if (pc = o, (mc = c) && !l) for (J = i; J !== null;) o = J, c = o.child, o.tag === 22 && o.memoizedState !== null || c === null ? zc(i) : (c.return = o, J = c);
					for (; a !== null;) J = a, Ic(a, t, n), a = a.sibling;
					J = i, pc = s, mc = l;
				}
				Lc(e, t, n);
			} else i.subtreeFlags & 8772 && a !== null ? (a.return = i, J = a) : Lc(e, t, n);
		}
	}
	function Lc(e) {
		for (; J !== null;) {
			var t = J;
			if (t.flags & 8772) {
				var n = t.alternate;
				try {
					if (t.flags & 8772) switch (t.tag) {
						case 0:
						case 11:
						case 15:
							mc || xc(5, t);
							break;
						case 1:
							var i = t.stateNode;
							if (t.flags & 4 && !mc) if (n === null) i.componentDidMount();
							else {
								var a = t.elementType === t.type ? n.memoizedProps : ys(t.type, n.memoizedProps);
								i.componentDidUpdate(a, n.memoizedState, i.__reactInternalSnapshotBeforeUpdate);
							}
							var o = t.updateQueue;
							o !== null && co(t, o, i);
							break;
						case 3:
							var s = t.updateQueue;
							if (s !== null) {
								if (n = null, t.child !== null) switch (t.child.tag) {
									case 5:
										n = t.child.stateNode;
										break;
									case 1: n = t.child.stateNode;
								}
								co(t, s, n);
							}
							break;
						case 5:
							var c = t.stateNode;
							if (n === null && t.flags & 4) {
								n = c;
								var l = t.memoizedProps;
								switch (t.type) {
									case "button":
									case "input":
									case "select":
									case "textarea":
										l.autoFocus && n.focus();
										break;
									case "img": l.src && (n.src = l.src);
								}
							}
							break;
						case 6: break;
						case 4: break;
						case 12: break;
						case 13:
							if (t.memoizedState === null) {
								var u = t.alternate;
								if (u !== null) {
									var d = u.memoizedState;
									if (d !== null) {
										var f = d.dehydrated;
										f !== null && hn(f);
									}
								}
							}
							break;
						case 19:
						case 17:
						case 21:
						case 22:
						case 23:
						case 25: break;
						default: throw Error(r(163));
					}
					mc || t.flags & 512 && Sc(t);
				} catch (e) {
					Vl(t, t.return, e);
				}
			}
			if (t === e) {
				J = null;
				break;
			}
			if (n = t.sibling, n !== null) {
				n.return = t.return, J = n;
				break;
			}
			J = t.return;
		}
	}
	function Rc(e) {
		for (; J !== null;) {
			var t = J;
			if (t === e) {
				J = null;
				break;
			}
			var n = t.sibling;
			if (n !== null) {
				n.return = t.return, J = n;
				break;
			}
			J = t.return;
		}
	}
	function zc(e) {
		for (; J !== null;) {
			var t = J;
			try {
				switch (t.tag) {
					case 0:
					case 11:
					case 15:
						var n = t.return;
						try {
							xc(4, t);
						} catch (e) {
							Vl(t, n, e);
						}
						break;
					case 1:
						var r = t.stateNode;
						if (typeof r.componentDidMount == "function") {
							var i = t.return;
							try {
								r.componentDidMount();
							} catch (e) {
								Vl(t, i, e);
							}
						}
						var a = t.return;
						try {
							Sc(t);
						} catch (e) {
							Vl(t, a, e);
						}
						break;
					case 5:
						var o = t.return;
						try {
							Sc(t);
						} catch (e) {
							Vl(t, o, e);
						}
				}
			} catch (e) {
				Vl(t, t.return, e);
			}
			if (t === e) {
				J = null;
				break;
			}
			var s = t.sibling;
			if (s !== null) {
				s.return = t.return, J = s;
				break;
			}
			J = t.return;
		}
	}
	var Bc = Math.ceil, Vc = C.ReactCurrentDispatcher, Hc = C.ReactCurrentOwner, Uc = C.ReactCurrentBatchConfig, X = 0, Wc = null, Gc = null, Kc = 0, qc = 0, Jc = qi(0), Yc = 0, Xc = null, Zc = 0, Qc = 0, $c = 0, el = null, tl = null, nl = 0, rl = Infinity, il = null, al = !1, ol = null, sl = null, cl = !1, ll = null, ul = 0, dl = 0, fl = null, pl = -1, ml = 0;
	function hl() {
		return X & 6 ? bt() : pl === -1 ? pl = bt() : pl;
	}
	function gl(e) {
		return e.mode & 1 ? X & 2 && Kc !== 0 ? Kc & -Kc : Fa.transition === null ? (e = L, e === 0 ? (e = window.event, e = e === void 0 ? 16 : Cn(e.type), e) : e) : (ml === 0 && (ml = Bt()), ml) : 1;
	}
	function _l(e, t, n, i) {
		if (50 < dl) throw dl = 0, fl = null, Error(r(185));
		Ht(e, n, i), (!(X & 2) || e !== Wc) && (e === Wc && (!(X & 2) && (Qc |= n), Yc === 4 && Cl(e, Kc)), vl(e, i), n === 1 && X === 0 && !(t.mode & 1) && (rl = bt() + 500, oa && ua()));
	}
	function vl(e, t) {
		var n = e.callbackNode;
		Rt(e, t);
		var r = It(e, e === Wc ? Kc : 0);
		if (r === 0) n !== null && _t(n), e.callbackNode = null, e.callbackPriority = 0;
		else if (t = r & -r, e.callbackPriority !== t) {
			if (n != null && _t(n), t === 1) e.tag === 0 ? la(wl.bind(null, e)) : ca(wl.bind(null, e)), ki(function() {
				!(X & 6) && ua();
			}), n = null;
			else {
				switch (Gt(r)) {
					case 1:
						n = St;
						break;
					case 4:
						n = Ct;
						break;
					case 16:
						n = wt;
						break;
					case 536870912:
						n = Et;
						break;
					default: n = wt;
				}
				n = ql(n, yl.bind(null, e));
			}
			e.callbackPriority = t, e.callbackNode = n;
		}
	}
	function yl(e, t) {
		if (pl = -1, ml = 0, X & 6) throw Error(r(327));
		var n = e.callbackNode;
		if (zl() && e.callbackNode !== n) return null;
		var i = It(e, e === Wc ? Kc : 0);
		if (i === 0) return null;
		if (i & 30 || (i & e.expiredLanes) !== 0 || t) t = Ml(e, i);
		else {
			t = i;
			var a = X;
			X |= 2;
			var o = Al();
			(Wc !== e || Kc !== t) && (il = null, rl = bt() + 500, Ol(e, t));
			do
				try {
					Pl();
					break;
				} catch (t) {
					kl(e, t);
				}
			while (1);
			Ga(), Vc.current = o, X = a, Gc === null ? (Wc = null, Kc = 0, t = Yc) : t = 0;
		}
		if (t !== 0) {
			if (t === 2 && (a = zt(e), a !== 0 && (i = a, t = bl(e, a))), t === 1) throw n = Xc, Ol(e, 0), Cl(e, i), vl(e, bt()), n;
			if (t === 6) Cl(e, i);
			else {
				if (a = e.current.alternate, !(i & 30) && !Sl(a) && (t = Ml(e, i), t === 2 && (o = zt(e), o !== 0 && (i = o, t = bl(e, o))), t === 1)) throw n = Xc, Ol(e, 0), Cl(e, i), vl(e, bt()), n;
				switch (e.finishedWork = a, e.finishedLanes = i, t) {
					case 0:
					case 1: throw Error(r(345));
					case 2:
						Ll(e, tl, il);
						break;
					case 3:
						if (Cl(e, i), (i & 130023424) === i && (t = nl + 500 - bt(), 10 < t)) {
							if (It(e, 0) !== 0) break;
							if (a = e.suspendedLanes, (a & i) !== i) {
								hl(), e.pingedLanes |= e.suspendedLanes & a;
								break;
							}
							e.timeoutHandle = Ei(Ll.bind(null, e, tl, il), t);
							break;
						}
						Ll(e, tl, il);
						break;
					case 4:
						if (Cl(e, i), (i & 4194240) === i) break;
						for (t = e.eventTimes, a = -1; 0 < i;) {
							var s = 31 - I(i);
							o = 1 << s, s = t[s], s > a && (a = s), i &= ~o;
						}
						if (i = a, i = bt() - i, i = (120 > i ? 120 : 480 > i ? 480 : 1080 > i ? 1080 : 1920 > i ? 1920 : 3e3 > i ? 3e3 : 4320 > i ? 4320 : 1960 * Bc(i / 1960)) - i, 10 < i) {
							e.timeoutHandle = Ei(Ll.bind(null, e, tl, il), i);
							break;
						}
						Ll(e, tl, il);
						break;
					case 5:
						Ll(e, tl, il);
						break;
					default: throw Error(r(329));
				}
			}
		}
		return vl(e, bt()), e.callbackNode === n ? yl.bind(null, e) : null;
	}
	function bl(e, t) {
		var n = el;
		return e.current.memoizedState.isDehydrated && (Ol(e, t).flags |= 256), e = Ml(e, t), e !== 2 && (t = tl, tl = n, t !== null && xl(t)), e;
	}
	function xl(e) {
		tl === null ? tl = e : tl.push.apply(tl, e);
	}
	function Sl(e) {
		for (var t = e;;) {
			if (t.flags & 16384) {
				var n = t.updateQueue;
				if (n !== null && (n = n.stores, n !== null)) for (var r = 0; r < n.length; r++) {
					var i = n[r], a = i.getSnapshot;
					i = i.value;
					try {
						if (!B(a(), i)) return !1;
					} catch (e) {
						return !1;
					}
				}
			}
			if (n = t.child, t.subtreeFlags & 16384 && n !== null) n.return = t, t = n;
			else {
				if (t === e) break;
				for (; t.sibling === null;) {
					if (t.return === null || t.return === e) return !0;
					t = t.return;
				}
				t.sibling.return = t.return, t = t.sibling;
			}
		}
		return !0;
	}
	function Cl(e, t) {
		for (t &= ~$c, t &= ~Qc, e.suspendedLanes |= t, e.pingedLanes &= ~t, e = e.expirationTimes; 0 < t;) {
			var n = 31 - I(t), r = 1 << n;
			e[n] = -1, t &= ~r;
		}
	}
	function wl(e) {
		if (X & 6) throw Error(r(327));
		zl();
		var t = It(e, 0);
		if (!(t & 1)) return vl(e, bt()), null;
		var n = Ml(e, t);
		if (e.tag !== 0 && n === 2) {
			var i = zt(e);
			i !== 0 && (t = i, n = bl(e, i));
		}
		if (n === 1) throw n = Xc, Ol(e, 0), Cl(e, t), vl(e, bt()), n;
		if (n === 6) throw Error(r(345));
		return e.finishedWork = e.current.alternate, e.finishedLanes = t, Ll(e, tl, il), vl(e, bt()), null;
	}
	function Tl(e, t) {
		var n = X;
		X |= 1;
		try {
			return e(t);
		} finally {
			X = n, X === 0 && (rl = bt() + 500, oa && ua());
		}
	}
	function El(e) {
		ll !== null && ll.tag === 0 && !(X & 6) && zl();
		var t = X;
		X |= 1;
		var n = Uc.transition, r = L;
		try {
			if (Uc.transition = null, L = 1, e) return e();
		} finally {
			L = r, Uc.transition = n, X = t, !(X & 6) && ua();
		}
	}
	function Dl() {
		qc = Jc.current, V(Jc);
	}
	function Ol(e, t) {
		e.finishedWork = null, e.finishedLanes = 0;
		var n = e.timeoutHandle;
		if (n !== -1 && (e.timeoutHandle = -1, Di(n)), Gc !== null) for (n = Gc.return; n !== null;) {
			var r = n;
			switch (Ca(r), r.tag) {
				case 1:
					r = r.type.childContextTypes, r != null && ea();
					break;
				case 3:
					go(), V(Xi), V(Yi), So();
					break;
				case 5:
					vo(r);
					break;
				case 4:
					go();
					break;
				case 13:
					V(yo);
					break;
				case 19:
					V(yo);
					break;
				case 10:
					Ka(r.type._context);
					break;
				case 22:
				case 23: Dl();
			}
			n = n.return;
		}
		if (Wc = e, Gc = e = Ql(e.current, null), Kc = qc = t, Yc = 0, Xc = null, $c = Qc = Zc = 0, tl = el = null, Xa !== null) {
			for (t = 0; t < Xa.length; t++) if (n = Xa[t], r = n.interleaved, r !== null) {
				n.interleaved = null;
				var i = r.next, a = n.pending;
				if (a !== null) {
					var o = a.next;
					a.next = i, r.next = o;
				}
				n.pending = r;
			}
			Xa = null;
		}
		return e;
	}
	function kl(e, t) {
		do {
			var n = Gc;
			try {
				if (Ga(), Co.current = hs, Oo) {
					for (var i = K.memoizedState; i !== null;) {
						var a = i.queue;
						a !== null && (a.pending = null), i = i.next;
					}
					Oo = !1;
				}
				if (To = 0, Do = Eo = K = null, ko = !1, Ao = 0, Hc.current = null, n === null || n.return === null) {
					Yc = 1, Xc = t, Gc = null;
					break;
				}
				a: {
					var o = e, s = n.return, c = n, l = t;
					if (t = Kc, c.flags |= 32768, typeof l == "object" && l && typeof l.then == "function") {
						var u = l, d = c, f = d.tag;
						if (!(d.mode & 1) && (f === 0 || f === 11 || f === 15)) {
							var p = d.alternate;
							p ? (d.updateQueue = p.updateQueue, d.memoizedState = p.memoizedState, d.lanes = p.lanes) : (d.updateQueue = null, d.memoizedState = null);
						}
						var m = Ns(s);
						if (m !== null) {
							m.flags &= -257, Ps(m, s, c, o, t), m.mode & 1 && Ms(o, u, t), t = m, l = u;
							var h = t.updateQueue;
							if (h === null) {
								var g = /* @__PURE__ */ new Set();
								g.add(l), t.updateQueue = g;
							} else h.add(l);
							break a;
						} else {
							if (!(t & 1)) {
								Ms(o, u, t), jl();
								break a;
							}
							l = Error(r(426));
						}
					} else if (U && c.mode & 1) {
						var _ = Ns(s);
						if (_ !== null) {
							!(_.flags & 65536) && (_.flags |= 256), Ps(_, s, c, o, t), Pa(Es(l, c));
							break a;
						}
					}
					o = l = Es(l, c), Yc !== 4 && (Yc = 2), el === null ? el = [o] : el.push(o), o = s;
					do {
						switch (o.tag) {
							case 3:
								o.flags |= 65536, t &= -t, o.lanes |= t;
								var v = As(o, l, t);
								oo(o, v);
								break a;
							case 1:
								c = l;
								var y = o.type, b = o.stateNode;
								if (!(o.flags & 128) && (typeof y.getDerivedStateFromError == "function" || b !== null && typeof b.componentDidCatch == "function" && (sl === null || !sl.has(b)))) {
									o.flags |= 65536, t &= -t, o.lanes |= t;
									var x = js(o, c, t);
									oo(o, x);
									break a;
								}
						}
						o = o.return;
					} while (o !== null);
				}
				Il(n);
			} catch (e) {
				t = e, Gc === n && n !== null && (Gc = n = n.return);
				continue;
			}
			break;
		} while (1);
	}
	function Al() {
		var e = Vc.current;
		return Vc.current = hs, e === null ? hs : e;
	}
	function jl() {
		(Yc === 0 || Yc === 3 || Yc === 2) && (Yc = 4), Wc === null || !(Zc & 268435455) && !(Qc & 268435455) || Cl(Wc, Kc);
	}
	function Ml(e, t) {
		var n = X;
		X |= 2;
		var i = Al();
		(Wc !== e || Kc !== t) && (il = null, Ol(e, t));
		do
			try {
				Nl();
				break;
			} catch (t) {
				kl(e, t);
			}
		while (1);
		if (Ga(), X = n, Vc.current = i, Gc !== null) throw Error(r(261));
		return Wc = null, Kc = 0, Yc;
	}
	function Nl() {
		for (; Gc !== null;) Fl(Gc);
	}
	function Pl() {
		for (; Gc !== null && !vt();) Fl(Gc);
	}
	function Fl(e) {
		var t = Kl(e.alternate, e, qc);
		e.memoizedProps = e.pendingProps, t === null ? Il(e) : Gc = t, Hc.current = null;
	}
	function Il(e) {
		var t = e;
		do {
			var n = t.alternate;
			if (e = t.return, t.flags & 32768) {
				if (n = fc(n, t), n !== null) {
					n.flags &= 32767, Gc = n;
					return;
				}
				if (e !== null) e.flags |= 32768, e.subtreeFlags = 0, e.deletions = null;
				else {
					Yc = 6, Gc = null;
					return;
				}
			} else if (n = dc(n, t, qc), n !== null) {
				Gc = n;
				return;
			}
			if (t = t.sibling, t !== null) {
				Gc = t;
				return;
			}
			Gc = t = e;
		} while (t !== null);
		Yc === 0 && (Yc = 5);
	}
	function Ll(e, t, n) {
		var r = L, i = Uc.transition;
		try {
			Uc.transition = null, L = 1, Rl(e, t, n, r);
		} finally {
			Uc.transition = i, L = r;
		}
		return null;
	}
	function Rl(e, t, n, i) {
		do
			zl();
		while (ll !== null);
		if (X & 6) throw Error(r(327));
		n = e.finishedWork;
		var a = e.finishedLanes;
		if (n === null) return null;
		if (e.finishedWork = null, e.finishedLanes = 0, n === e.current) throw Error(r(177));
		e.callbackNode = null, e.callbackPriority = 0;
		var o = n.lanes | n.childLanes;
		if (Ut(e, o), e === Wc && (Gc = Wc = null, Kc = 0), !(n.subtreeFlags & 2064) && !(n.flags & 2064) || cl || (cl = !0, ql(wt, function() {
			return zl(), null;
		})), o = (n.flags & 15990) != 0, n.subtreeFlags & 15990 || o) {
			o = Uc.transition, Uc.transition = null;
			var s = L;
			L = 1;
			var c = X;
			X |= 4, Hc.current = null, yc(e, n), Nc(n, e), Lr(wi), _n = !!Ci, wi = Ci = null, e.current = n, Fc(n, e, a), yt(), X = c, L = s, Uc.transition = o;
		} else e.current = n;
		if (cl && (cl = !1, ll = e, ul = a), o = e.pendingLanes, o === 0 && (sl = null), kt(n.stateNode, i), vl(e, bt()), t !== null) for (i = e.onRecoverableError, n = 0; n < t.length; n++) a = t[n], i(a.value, {
			componentStack: a.stack,
			digest: a.digest
		});
		if (al) throw al = !1, e = ol, ol = null, e;
		return ul & 1 && e.tag !== 0 && zl(), o = e.pendingLanes, o & 1 ? e === fl ? dl++ : (dl = 0, fl = e) : dl = 0, ua(), null;
	}
	function zl() {
		if (ll !== null) {
			var e = Gt(ul), t = Uc.transition, n = L;
			try {
				if (Uc.transition = null, L = 16 > e ? 16 : e, ll === null) var i = !1;
				else {
					if (e = ll, ll = null, ul = 0, X & 6) throw Error(r(331));
					var a = X;
					for (X |= 4, J = e.current; J !== null;) {
						var o = J, s = o.child;
						if (J.flags & 16) {
							var c = o.deletions;
							if (c !== null) {
								for (var l = 0; l < c.length; l++) {
									var u = c[l];
									for (J = u; J !== null;) {
										var d = J;
										switch (d.tag) {
											case 0:
											case 11:
											case 15: bc(8, d, o);
										}
										var f = d.child;
										if (f !== null) f.return = d, J = f;
										else for (; J !== null;) {
											d = J;
											var p = d.sibling, m = d.return;
											if (Cc(d), d === u) {
												J = null;
												break;
											}
											if (p !== null) {
												p.return = m, J = p;
												break;
											}
											J = m;
										}
									}
								}
								var h = o.alternate;
								if (h !== null) {
									var g = h.child;
									if (g !== null) {
										h.child = null;
										do {
											var _ = g.sibling;
											g.sibling = null, g = _;
										} while (g !== null);
									}
								}
								J = o;
							}
						}
						if (o.subtreeFlags & 2064 && s !== null) s.return = o, J = s;
						else b: for (; J !== null;) {
							if (o = J, o.flags & 2048) switch (o.tag) {
								case 0:
								case 11:
								case 15: bc(9, o, o.return);
							}
							var v = o.sibling;
							if (v !== null) {
								v.return = o.return, J = v;
								break b;
							}
							J = o.return;
						}
					}
					var y = e.current;
					for (J = y; J !== null;) {
						s = J;
						var b = s.child;
						if (s.subtreeFlags & 2064 && b !== null) b.return = s, J = b;
						else b: for (s = y; J !== null;) {
							if (c = J, c.flags & 2048) try {
								switch (c.tag) {
									case 0:
									case 11:
									case 15: xc(9, c);
								}
							} catch (e) {
								Vl(c, c.return, e);
							}
							if (c === s) {
								J = null;
								break b;
							}
							var x = c.sibling;
							if (x !== null) {
								x.return = c.return, J = x;
								break b;
							}
							J = c.return;
						}
					}
					if (X = a, ua(), Ot && typeof Ot.onPostCommitFiberRoot == "function") try {
						Ot.onPostCommitFiberRoot(Dt, e);
					} catch (e) {}
					i = !0;
				}
				return i;
			} finally {
				L = n, Uc.transition = t;
			}
		}
		return !1;
	}
	function Bl(e, t, n) {
		t = Es(n, t), t = As(e, t, 1), e = io(e, t, 1), t = hl(), e !== null && (Ht(e, 1, t), vl(e, t));
	}
	function Vl(e, t, n) {
		if (e.tag === 3) Bl(e, e, n);
		else for (; t !== null;) {
			if (t.tag === 3) {
				Bl(t, e, n);
				break;
			} else if (t.tag === 1) {
				var r = t.stateNode;
				if (typeof t.type.getDerivedStateFromError == "function" || typeof r.componentDidCatch == "function" && (sl === null || !sl.has(r))) {
					e = Es(n, e), e = js(t, e, 1), t = io(t, e, 1), e = hl(), t !== null && (Ht(t, 1, e), vl(t, e));
					break;
				}
			}
			t = t.return;
		}
	}
	function Hl(e, t, n) {
		var r = e.pingCache;
		r !== null && r.delete(t), t = hl(), e.pingedLanes |= e.suspendedLanes & n, Wc === e && (Kc & n) === n && (Yc === 4 || Yc === 3 && (Kc & 130023424) === Kc && 500 > bt() - nl ? Ol(e, 0) : $c |= n), vl(e, t);
	}
	function Ul(e, t) {
		t === 0 && (e.mode & 1 ? (t = Pt, Pt <<= 1, !(Pt & 130023424) && (Pt = 4194304)) : t = 1);
		var n = hl();
		e = $a(e, t), e !== null && (Ht(e, t, n), vl(e, n));
	}
	function Wl(e) {
		var t = e.memoizedState, n = 0;
		t !== null && (n = t.retryLane), Ul(e, n);
	}
	function Gl(e, t) {
		var n = 0;
		switch (e.tag) {
			case 13:
				var i = e.stateNode, a = e.memoizedState;
				a !== null && (n = a.retryLane);
				break;
			case 19:
				i = e.stateNode;
				break;
			default: throw Error(r(314));
		}
		i !== null && i.delete(t), Ul(e, n);
	}
	var Kl = function(e, t, n) {
		if (e !== null) if (e.memoizedProps !== t.pendingProps || Xi.current) Is = !0;
		else {
			if ((e.lanes & n) === 0 && !(t.flags & 128)) return Is = !1, ac(e, t, n);
			Is = !!(e.flags & 131072);
		}
		else Is = !1, U && t.flags & 1048576 && xa(t, ma, t.index);
		switch (t.lanes = 0, t.tag) {
			case 2:
				var i = t.type;
				rc(e, t), e = t.pendingProps;
				var a = Qi(t, Yi.current);
				Ja(t, n), a = Po(null, t, i, e, a, n);
				var o = Fo();
				return t.flags |= 1, typeof a == "object" && a && typeof a.render == "function" && a.$$typeof === void 0 ? (t.tag = 1, t.memoizedState = null, t.updateQueue = null, $i(i) ? (o = !0, ra(t)) : o = !1, t.memoizedState = a.state !== null && a.state !== void 0 ? a.state : null, to(t), a.updater = xs, t.stateNode = a, a._reactInternals = t, Ts(t, i, e, n), t = Gs(null, t, i, !0, o, n)) : (t.tag = 0, U && o && Sa(t), Ls(null, t, a, n), t = t.child), t;
			case 16:
				i = t.elementType;
				a: {
					switch (rc(e, t), e = t.pendingProps, a = i._init, i = a(i._payload), t.type = i, a = t.tag = Zl(i), e = ys(i, e), a) {
						case 0:
							t = Us(null, t, i, e, n);
							break a;
						case 1:
							t = Ws(null, t, i, e, n);
							break a;
						case 11:
							t = Rs(null, t, i, e, n);
							break a;
						case 14:
							t = zs(null, t, i, ys(i.type, e), n);
							break a;
					}
					throw Error(r(306, i, ""));
				}
				return t;
			case 0: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ys(i, a), Us(e, t, i, a, n);
			case 1: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ys(i, a), Ws(e, t, i, a, n);
			case 3:
				a: {
					if (Ks(t), e === null) throw Error(r(387));
					i = t.pendingProps, o = t.memoizedState, a = o.element, no(e, t), so(t, i, null, n);
					var s = t.memoizedState;
					if (i = s.element, o.isDehydrated) if (o = {
						element: i,
						isDehydrated: !1,
						cache: s.cache,
						pendingSuspenseBoundaries: s.pendingSuspenseBoundaries,
						transitions: s.transitions
					}, t.updateQueue.baseState = o, t.memoizedState = o, t.flags & 256) {
						a = Es(Error(r(423)), t), t = qs(e, t, i, n, a);
						break a;
					} else if (i !== a) {
						a = Es(Error(r(424)), t), t = qs(e, t, i, n, a);
						break a;
					} else for (Ta = Mi(t.stateNode.containerInfo.firstChild), wa = t, U = !0, Ea = null, n = Ba(t, null, i, n), t.child = n; n;) n.flags = n.flags & -3 | 4096, n = n.sibling;
					else {
						if (Na(), i === a) {
							t = ic(e, t, n);
							break a;
						}
						Ls(e, t, i, n);
					}
					t = t.child;
				}
				return t;
			case 5: return _o(t), e === null && ka(t), i = t.type, a = t.pendingProps, o = e === null ? null : e.memoizedProps, s = a.children, Ti(i, a) ? s = null : o !== null && Ti(i, o) && (t.flags |= 32), Hs(e, t), Ls(e, t, s, n), t.child;
			case 6: return e === null && ka(t), null;
			case 13: return Xs(e, t, n);
			case 4: return ho(t, t.stateNode.containerInfo), i = t.pendingProps, e === null ? t.child = G(t, null, i, n) : Ls(e, t, i, n), t.child;
			case 11: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ys(i, a), Rs(e, t, i, a, n);
			case 7: return Ls(e, t, t.pendingProps, n), t.child;
			case 8: return Ls(e, t, t.pendingProps.children, n), t.child;
			case 12: return Ls(e, t, t.pendingProps.children, n), t.child;
			case 10:
				a: {
					if (i = t.type._context, a = t.pendingProps, o = t.memoizedProps, s = a.value, H(Va, i._currentValue), i._currentValue = s, o !== null) if (B(o.value, s)) {
						if (o.children === a.children && !Xi.current) {
							t = ic(e, t, n);
							break a;
						}
					} else for (o = t.child, o !== null && (o.return = t); o !== null;) {
						var c = o.dependencies;
						if (c !== null) {
							s = o.child;
							for (var l = c.firstContext; l !== null;) {
								if (l.context === i) {
									if (o.tag === 1) {
										l = ro(-1, n & -n), l.tag = 2;
										var u = o.updateQueue;
										if (u !== null) {
											u = u.shared;
											var d = u.pending;
											d === null ? l.next = l : (l.next = d.next, d.next = l), u.pending = l;
										}
									}
									o.lanes |= n, l = o.alternate, l !== null && (l.lanes |= n), qa(o.return, n, t), c.lanes |= n;
									break;
								}
								l = l.next;
							}
						} else if (o.tag === 10) s = o.type === t.type ? null : o.child;
						else if (o.tag === 18) {
							if (s = o.return, s === null) throw Error(r(341));
							s.lanes |= n, c = s.alternate, c !== null && (c.lanes |= n), qa(s, n, t), s = o.sibling;
						} else s = o.child;
						if (s !== null) s.return = o;
						else for (s = o; s !== null;) {
							if (s === t) {
								s = null;
								break;
							}
							if (o = s.sibling, o !== null) {
								o.return = s.return, s = o;
								break;
							}
							s = s.return;
						}
						o = s;
					}
					Ls(e, t, a.children, n), t = t.child;
				}
				return t;
			case 9: return a = t.type, i = t.pendingProps.children, Ja(t, n), a = Ya(a), i = i(a), t.flags |= 1, Ls(e, t, i, n), t.child;
			case 14: return i = t.type, a = ys(i, t.pendingProps), a = ys(i.type, a), zs(e, t, i, a, n);
			case 15: return Bs(e, t, t.type, t.pendingProps, n);
			case 17: return i = t.type, a = t.pendingProps, a = t.elementType === i ? a : ys(i, a), rc(e, t), t.tag = 1, $i(i) ? (e = !0, ra(t)) : e = !1, Ja(t, n), Cs(t, i, a), Ts(t, i, a, n), Gs(null, t, i, !0, e, n);
			case 19: return nc(e, t, n);
			case 22: return Vs(e, t, n);
		}
		throw Error(r(156, t.tag));
	};
	function ql(e, t) {
		return gt(e, t);
	}
	function Jl(e, t, n, r) {
		this.tag = e, this.key = n, this.sibling = this.child = this.return = this.stateNode = this.type = this.elementType = null, this.index = 0, this.ref = null, this.pendingProps = t, this.dependencies = this.memoizedState = this.updateQueue = this.memoizedProps = null, this.mode = r, this.subtreeFlags = this.flags = 0, this.deletions = null, this.childLanes = this.lanes = 0, this.alternate = null;
	}
	function Yl(e, t, n, r) {
		return new Jl(e, t, n, r);
	}
	function Xl(e) {
		return e = e.prototype, !(!e || !e.isReactComponent);
	}
	function Zl(e) {
		if (typeof e == "function") return +!!Xl(e);
		if (e != null) {
			if (e = e.$$typeof, e === j) return 11;
			if (e === P) return 14;
		}
		return 2;
	}
	function Ql(e, t) {
		var n = e.alternate;
		return n === null ? (n = Yl(e.tag, t, e.key, e.mode), n.elementType = e.elementType, n.type = e.type, n.stateNode = e.stateNode, n.alternate = e, e.alternate = n) : (n.pendingProps = t, n.type = e.type, n.flags = 0, n.subtreeFlags = 0, n.deletions = null), n.flags = e.flags & 14680064, n.childLanes = e.childLanes, n.lanes = e.lanes, n.child = e.child, n.memoizedProps = e.memoizedProps, n.memoizedState = e.memoizedState, n.updateQueue = e.updateQueue, t = e.dependencies, n.dependencies = t === null ? null : {
			lanes: t.lanes,
			firstContext: t.firstContext
		}, n.sibling = e.sibling, n.index = e.index, n.ref = e.ref, n;
	}
	function $l(e, t, n, i, a, o) {
		var s = 2;
		if (i = e, typeof e == "function") Xl(e) && (s = 1);
		else if (typeof e == "string") s = 5;
		else a: switch (e) {
			case E: return eu(n.children, a, o, t);
			case D:
				s = 8, a |= 8;
				break;
			case O: return e = Yl(12, n, t, a | 2), e.elementType = O, e.lanes = o, e;
			case M: return e = Yl(13, n, t, a), e.elementType = M, e.lanes = o, e;
			case N: return e = Yl(19, n, t, a), e.elementType = N, e.lanes = o, e;
			case te: return tu(n, a, o, t);
			default:
				if (typeof e == "object" && e) switch (e.$$typeof) {
					case k:
						s = 10;
						break a;
					case A:
						s = 9;
						break a;
					case j:
						s = 11;
						break a;
					case P:
						s = 14;
						break a;
					case ee:
						s = 16, i = null;
						break a;
				}
				throw Error(r(130, e == null ? e : typeof e, ""));
		}
		return t = Yl(s, n, t, a), t.elementType = e, t.type = i, t.lanes = o, t;
	}
	function eu(e, t, n, r) {
		return e = Yl(7, e, r, t), e.lanes = n, e;
	}
	function tu(e, t, n, r) {
		return e = Yl(22, e, r, t), e.elementType = te, e.lanes = n, e.stateNode = { isHidden: !1 }, e;
	}
	function nu(e, t, n) {
		return e = Yl(6, e, null, t), e.lanes = n, e;
	}
	function ru(e, t, n) {
		return t = Yl(4, e.children === null ? [] : e.children, e.key, t), t.lanes = n, t.stateNode = {
			containerInfo: e.containerInfo,
			pendingChildren: null,
			implementation: e.implementation
		}, t;
	}
	function iu(e, t, n, r, i) {
		this.tag = t, this.containerInfo = e, this.finishedWork = this.pingCache = this.current = this.pendingChildren = null, this.timeoutHandle = -1, this.callbackNode = this.pendingContext = this.context = null, this.callbackPriority = 0, this.eventTimes = Vt(0), this.expirationTimes = Vt(-1), this.entangledLanes = this.finishedLanes = this.mutableReadLanes = this.expiredLanes = this.pingedLanes = this.suspendedLanes = this.pendingLanes = 0, this.entanglements = Vt(0), this.identifierPrefix = r, this.onRecoverableError = i, this.mutableSourceEagerHydrationData = null;
	}
	function au(e, t, n, r, i, a, o, s, c) {
		return e = new iu(e, t, n, s, c), t === 1 ? (t = 1, !0 === a && (t |= 8)) : t = 0, a = Yl(3, null, null, t), e.current = a, a.stateNode = e, a.memoizedState = {
			element: r,
			isDehydrated: n,
			cache: null,
			transitions: null,
			pendingSuspenseBoundaries: null
		}, to(a), e;
	}
	function ou(e, t, n) {
		var r = 3 < arguments.length && arguments[3] !== void 0 ? arguments[3] : null;
		return {
			$$typeof: T,
			key: r == null ? null : "" + r,
			children: e,
			containerInfo: t,
			implementation: n
		};
	}
	function su(e) {
		if (!e) return Ji;
		e = e._reactInternals;
		a: {
			if (ut(e) !== e || e.tag !== 1) throw Error(r(170));
			var t = e;
			do {
				switch (t.tag) {
					case 3:
						t = t.stateNode.context;
						break a;
					case 1: if ($i(t.type)) {
						t = t.stateNode.__reactInternalMemoizedMergedChildContext;
						break a;
					}
				}
				t = t.return;
			} while (t !== null);
			throw Error(r(171));
		}
		if (e.tag === 1) {
			var n = e.type;
			if ($i(n)) return na(e, n, t);
		}
		return t;
	}
	function cu(e, t, n, r, i, a, o, s, c) {
		return e = au(n, r, !0, e, i, a, o, s, c), e.context = su(null), n = e.current, r = hl(), i = gl(n), a = ro(r, i), a.callback = t == null ? null : t, io(n, a, i), e.current.lanes = i, Ht(e, i, r), vl(e, r), e;
	}
	function lu(e, t, n, r) {
		var i = t.current, a = hl(), o = gl(i);
		return n = su(n), t.context === null ? t.context = n : t.pendingContext = n, t = ro(a, o), t.payload = { element: e }, r = r === void 0 ? null : r, r !== null && (t.callback = r), e = io(i, t, o), e !== null && (_l(e, i, o, a), ao(e, i, o)), o;
	}
	function uu(e) {
		if (e = e.current, !e.child) return null;
		switch (e.child.tag) {
			case 5: return e.child.stateNode;
			default: return e.child.stateNode;
		}
	}
	function du(e, t) {
		if (e = e.memoizedState, e !== null && e.dehydrated !== null) {
			var n = e.retryLane;
			e.retryLane = n !== 0 && n < t ? n : t;
		}
	}
	function fu(e, t) {
		du(e, t), (e = e.alternate) && du(e, t);
	}
	function pu() {
		return null;
	}
	var mu = typeof reportError == "function" ? reportError : function(e) {
		console.error(e);
	};
	function hu(e) {
		this._internalRoot = e;
	}
	gu.prototype.render = hu.prototype.render = function(e) {
		var t = this._internalRoot;
		if (t === null) throw Error(r(409));
		lu(e, t, null, null);
	}, gu.prototype.unmount = hu.prototype.unmount = function() {
		var e = this._internalRoot;
		if (e !== null) {
			this._internalRoot = null;
			var t = e.containerInfo;
			El(function() {
				lu(null, e, null, null);
			}), t[Li] = null;
		}
	};
	function gu(e) {
		this._internalRoot = e;
	}
	gu.prototype.unstable_scheduleHydration = function(e) {
		if (e) {
			var t = Yt();
			e = {
				blockedOn: null,
				target: e,
				priority: t
			};
			for (var n = 0; n < an.length && t !== 0 && t < an[n].priority; n++);
			an.splice(n, 0, e), n === 0 && un(e);
		}
	};
	function _u(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11);
	}
	function vu(e) {
		return !(!e || e.nodeType !== 1 && e.nodeType !== 9 && e.nodeType !== 11 && (e.nodeType !== 8 || e.nodeValue !== " react-mount-point-unstable "));
	}
	function yu() {}
	function bu(e, t, n, r, i) {
		if (i) {
			if (typeof r == "function") {
				var a = r;
				r = function() {
					var e = uu(o);
					a.call(e);
				};
			}
			var o = cu(t, r, e, 0, null, !1, !1, "", yu);
			return e._reactRootContainer = o, e[Li] = o.current, di(e.nodeType === 8 ? e.parentNode : e), El(), o;
		}
		for (; i = e.lastChild;) e.removeChild(i);
		if (typeof r == "function") {
			var s = r;
			r = function() {
				var e = uu(c);
				s.call(e);
			};
		}
		var c = au(e, 0, !1, null, null, !1, !1, "", yu);
		return e._reactRootContainer = c, e[Li] = c.current, di(e.nodeType === 8 ? e.parentNode : e), El(function() {
			lu(t, c, n, r);
		}), c;
	}
	function xu(e, t, n, r, i) {
		var a = n._reactRootContainer;
		if (a) {
			var o = a;
			if (typeof i == "function") {
				var s = i;
				i = function() {
					var e = uu(o);
					s.call(e);
				};
			}
			lu(t, o, e, i);
		} else o = bu(n, t, e, i, r);
		return uu(o);
	}
	Kt = function(e) {
		switch (e.tag) {
			case 3:
				var t = e.stateNode;
				if (t.current.memoizedState.isDehydrated) {
					var n = Ft(t.pendingLanes);
					n !== 0 && (Wt(t, n | 1), vl(t, bt()), !(X & 6) && (rl = bt() + 500, ua()));
				}
				break;
			case 13: El(function() {
				var t = $a(e, 1);
				t !== null && _l(t, e, 1, hl());
			}), fu(e, 1);
		}
	}, qt = function(e) {
		if (e.tag === 13) {
			var t = $a(e, 134217728);
			t !== null && _l(t, e, 134217728, hl()), fu(e, 134217728);
		}
	}, Jt = function(e) {
		if (e.tag === 13) {
			var t = gl(e), n = $a(e, t);
			n !== null && _l(n, e, t, hl()), fu(e, t);
		}
	}, Yt = function() {
		return L;
	}, Xt = function(e, t) {
		var n = L;
		try {
			return L = e, t();
		} finally {
			L = n;
		}
	}, Ue = function(e, t, n) {
		switch (t) {
			case "input":
				if (be(e, n), t = n.name, n.type === "radio" && t != null) {
					for (n = e; n.parentNode;) n = n.parentNode;
					for (n = n.querySelectorAll("input[name=" + JSON.stringify("" + t) + "][type=\"radio\"]"), t = 0; t < n.length; t++) {
						var i = n[t];
						if (i !== e && i.form === e.form) {
							var a = Wi(i);
							if (!a) throw Error(r(90));
							he(i), be(i, a);
						}
					}
				}
				break;
			case "textarea":
				De(e, n);
				break;
			case "select": t = n.value, t != null && we(e, !!n.multiple, t, !1);
		}
	}, Ye = Tl, Xe = El;
	var Su = {
		usingClientEntryPoint: !1,
		Events: [
			Hi,
			Ui,
			Wi,
			qe,
			Je,
			Tl
		]
	}, Cu = {
		findFiberByHostInstance: Vi,
		bundleType: 0,
		version: "18.3.1",
		rendererPackageName: "react-dom"
	}, wu = {
		bundleType: Cu.bundleType,
		version: Cu.version,
		rendererPackageName: Cu.rendererPackageName,
		rendererConfig: Cu.rendererConfig,
		overrideHookState: null,
		overrideHookStateDeletePath: null,
		overrideHookStateRenamePath: null,
		overrideProps: null,
		overridePropsDeletePath: null,
		overridePropsRenamePath: null,
		setErrorHandler: null,
		setSuspenseHandler: null,
		scheduleUpdate: null,
		currentDispatcherRef: C.ReactCurrentDispatcher,
		findHostInstanceByFiber: function(e) {
			return e = mt(e), e === null ? null : e.stateNode;
		},
		findFiberByHostInstance: Cu.findFiberByHostInstance || pu,
		findHostInstancesForRefresh: null,
		scheduleRefresh: null,
		scheduleRoot: null,
		setRefreshHandler: null,
		getCurrentFiber: null,
		reconcilerVersion: "18.3.1-next-f1338f8080-20240426"
	};
	if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ < "u") {
		var Tu = __REACT_DEVTOOLS_GLOBAL_HOOK__;
		if (!Tu.isDisabled && Tu.supportsFiber) try {
			Dt = Tu.inject(wu), Ot = Tu;
		} catch (e) {}
	}
	e.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = Su, e.createPortal = function(e, t) {
		var n = 2 < arguments.length && arguments[2] !== void 0 ? arguments[2] : null;
		if (!_u(t)) throw Error(r(200));
		return ou(e, t, null, n);
	}, e.createRoot = function(e, t) {
		if (!_u(e)) throw Error(r(299));
		var n = !1, i = "", a = mu;
		return t != null && (!0 === t.unstable_strictMode && (n = !0), t.identifierPrefix !== void 0 && (i = t.identifierPrefix), t.onRecoverableError !== void 0 && (a = t.onRecoverableError)), t = au(e, 1, !1, null, null, n, !1, i, a), e[Li] = t.current, di(e.nodeType === 8 ? e.parentNode : e), new hu(t);
	}, e.findDOMNode = function(e) {
		if (e == null) return null;
		if (e.nodeType === 1) return e;
		var t = e._reactInternals;
		if (t === void 0) throw typeof e.render == "function" ? Error(r(188)) : (e = Object.keys(e).join(","), Error(r(268, e)));
		return e = mt(t), e = e === null ? null : e.stateNode, e;
	}, e.flushSync = function(e) {
		return El(e);
	}, e.hydrate = function(e, t, n) {
		if (!vu(t)) throw Error(r(200));
		return xu(null, e, t, !0, n);
	}, e.hydrateRoot = function(e, t, n) {
		if (!_u(e)) throw Error(r(405));
		var i = n != null && n.hydratedSources || null, a = !1, o = "", s = mu;
		if (n != null && (!0 === n.unstable_strictMode && (a = !0), n.identifierPrefix !== void 0 && (o = n.identifierPrefix), n.onRecoverableError !== void 0 && (s = n.onRecoverableError)), t = cu(t, null, e, 1, n == null ? null : n, a, !1, o, s), e[Li] = t.current, di(e), i) for (e = 0; e < i.length; e++) n = i[e], a = n._getVersion, a = a(n._source), t.mutableSourceEagerHydrationData == null ? t.mutableSourceEagerHydrationData = [n, a] : t.mutableSourceEagerHydrationData.push(n, a);
		return new gu(t);
	}, e.render = function(e, t, n) {
		if (!vu(t)) throw Error(r(200));
		return xu(null, e, t, !1, n);
	}, e.unmountComponentAtNode = function(e) {
		if (!vu(e)) throw Error(r(40));
		return e._reactRootContainer ? (El(function() {
			xu(null, null, e, !1, function() {
				e._reactRootContainer = null, e[Li] = null;
			});
		}), !0) : !1;
	}, e.unstable_batchedUpdates = Tl, e.unstable_renderSubtreeIntoContainer = function(e, t, n, i) {
		if (!vu(n)) throw Error(r(200));
		if (e == null || e._reactInternals === void 0) throw Error(r(38));
		return xu(e, t, n, !1, i);
	}, e.version = "18.3.1-next-f1338f8080-20240426";
})), h = /* @__PURE__ */ o(((e, t) => {
	function n() {
		if (!(typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ > "u" || typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE != "function")) try {
			__REACT_DEVTOOLS_GLOBAL_HOOK__.checkDCE(n);
		} catch (e) {
			console.error(e);
		}
	}
	n(), t.exports = m();
})), g = /* @__PURE__ */ o(((e) => {
	var t = h();
	e.createRoot = t.createRoot, e.hydrateRoot = t.hydrateRoot;
})), _ = (...e) => e.filter((e, t, n) => !!e && e.trim() !== "" && n.indexOf(e) === t).join(" ").trim(), v = (e) => e.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase(), y = (e) => e.replace(/^([A-Z])|[\s-_]+(\w)/g, (e, t, n) => n ? n.toUpperCase() : t.toLowerCase()), b = (e) => {
	let t = y(e);
	return t.charAt(0).toUpperCase() + t.slice(1);
}, x = {
	xmlns: "http://www.w3.org/2000/svg",
	width: 24,
	height: 24,
	viewBox: "0 0 24 24",
	fill: "none",
	stroke: "currentColor",
	strokeWidth: 2,
	strokeLinecap: "round",
	strokeLinejoin: "round"
}, S = (e) => {
	for (let t in e) if (t.startsWith("aria-") || t === "role" || t === "title") return !0;
	return !1;
}, C = /* @__PURE__ */ l(d(), 1), w = (0, C.createContext)({}), T = () => (0, C.useContext)(w), E = (0, C.forwardRef)(({ color: e, size: t, strokeWidth: n, absoluteStrokeWidth: r, className: i = "", children: a, iconNode: o, ...s }, c) => {
	var l, u, d;
	let { size: f = 24, strokeWidth: p = 2, absoluteStrokeWidth: m = !1, color: h = "currentColor", className: g = "" } = (l = T()) == null ? {} : l, v = (r == null ? m : r) ? Number(n == null ? p : n) * 24 / Number(t == null ? f : t) : n == null ? p : n;
	return (0, C.createElement)("svg", {
		ref: c,
		...x,
		width: (u = t == null ? f : t) == null ? x.width : u,
		height: (d = t == null ? f : t) == null ? x.height : d,
		stroke: e == null ? h : e,
		strokeWidth: v,
		className: _("lucide", g, i),
		...!a && !S(s) && { "aria-hidden": "true" },
		...s
	}, [...o.map(([e, t]) => (0, C.createElement)(e, t)), ...Array.isArray(a) ? a : [a]]);
}), D = (e, t) => {
	let n = (0, C.forwardRef)(({ className: n, ...r }, i) => (0, C.createElement)(E, {
		ref: i,
		iconNode: t,
		className: _(`lucide-${v(b(e))}`, `lucide-${e}`, n),
		...r
	}));
	return n.displayName = b(e), n;
}, O = D("list-checks", [
	["path", {
		d: "M13 5h8",
		key: "a7qcls"
	}],
	["path", {
		d: "M13 12h8",
		key: "h98zly"
	}],
	["path", {
		d: "M13 19h8",
		key: "c3s6r1"
	}],
	["path", {
		d: "m3 17 2 2 4-4",
		key: "1jhpwq"
	}],
	["path", {
		d: "m3 7 2 2 4-4",
		key: "1obspn"
	}]
]), k = D("messages-square", [["path", {
	d: "M16 10a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 14.286V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",
	key: "1n2ejm"
}], ["path", {
	d: "M20 9a2 2 0 0 1 2 2v10.286a.71.71 0 0 1-1.212.502l-2.202-2.202A2 2 0 0 0 17.172 19H10a2 2 0 0 1-2-2v-1",
	key: "1qfcsi"
}]]), A = D("rows-3", [
	["rect", {
		width: "18",
		height: "18",
		x: "3",
		y: "3",
		rx: "2",
		key: "afitv7"
	}],
	["path", {
		d: "M21 9H3",
		key: "1338ky"
	}],
	["path", {
		d: "M21 15H3",
		key: "9uk58r"
	}]
]), j = D("wand-sparkles", [
	["path", {
		d: "m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72",
		key: "ul74o6"
	}],
	["path", {
		d: "m14 7 3 3",
		key: "1r5n42"
	}],
	["path", {
		d: "M5 6v4",
		key: "ilb8ba"
	}],
	["path", {
		d: "M19 14v4",
		key: "blhpug"
	}],
	["path", {
		d: "M10 2v2",
		key: "7u0qdc"
	}],
	["path", {
		d: "M7 8H3",
		key: "zfb6yr"
	}],
	["path", {
		d: "M21 16h-4",
		key: "1cnmox"
	}],
	["path", {
		d: "M11 3H9",
		key: "1obp7u"
	}]
]);
//#endregion
//#region node_modules/clsx/dist/clsx.mjs
function M(e) {
	var t, n, r = "";
	if (typeof e == "string" || typeof e == "number") r += e;
	else if (typeof e == "object") if (Array.isArray(e)) {
		var i = e.length;
		for (t = 0; t < i; t++) e[t] && (n = M(e[t])) && (r && (r += " "), r += n);
	} else for (n in e) e[n] && (r && (r += " "), r += n);
	return r;
}
function N() {
	for (var e, t, n = 0, r = "", i = arguments.length; n < i; n++) (e = arguments[n]) && (t = M(e)) && (r && (r += " "), r += t);
	return r;
}
//#endregion
//#region node_modules/recharts/es6/util/excludeEventProps.js
var P = /* @__PURE__ */ "dangerouslySetInnerHTML.onCopy.onCopyCapture.onCut.onCutCapture.onPaste.onPasteCapture.onCompositionEnd.onCompositionEndCapture.onCompositionStart.onCompositionStartCapture.onCompositionUpdate.onCompositionUpdateCapture.onFocus.onFocusCapture.onBlur.onBlurCapture.onChange.onChangeCapture.onBeforeInput.onBeforeInputCapture.onInput.onInputCapture.onReset.onResetCapture.onSubmit.onSubmitCapture.onInvalid.onInvalidCapture.onLoad.onLoadCapture.onError.onErrorCapture.onKeyDown.onKeyDownCapture.onKeyPress.onKeyPressCapture.onKeyUp.onKeyUpCapture.onAbort.onAbortCapture.onCanPlay.onCanPlayCapture.onCanPlayThrough.onCanPlayThroughCapture.onDurationChange.onDurationChangeCapture.onEmptied.onEmptiedCapture.onEncrypted.onEncryptedCapture.onEnded.onEndedCapture.onLoadedData.onLoadedDataCapture.onLoadedMetadata.onLoadedMetadataCapture.onLoadStart.onLoadStartCapture.onPause.onPauseCapture.onPlay.onPlayCapture.onPlaying.onPlayingCapture.onProgress.onProgressCapture.onRateChange.onRateChangeCapture.onSeeked.onSeekedCapture.onSeeking.onSeekingCapture.onStalled.onStalledCapture.onSuspend.onSuspendCapture.onTimeUpdate.onTimeUpdateCapture.onVolumeChange.onVolumeChangeCapture.onWaiting.onWaitingCapture.onAuxClick.onAuxClickCapture.onClick.onClickCapture.onContextMenu.onContextMenuCapture.onDoubleClick.onDoubleClickCapture.onDrag.onDragCapture.onDragEnd.onDragEndCapture.onDragEnter.onDragEnterCapture.onDragExit.onDragExitCapture.onDragLeave.onDragLeaveCapture.onDragOver.onDragOverCapture.onDragStart.onDragStartCapture.onDrop.onDropCapture.onMouseDown.onMouseDownCapture.onMouseEnter.onMouseLeave.onMouseMove.onMouseMoveCapture.onMouseOut.onMouseOutCapture.onMouseOver.onMouseOverCapture.onMouseUp.onMouseUpCapture.onSelect.onSelectCapture.onTouchCancel.onTouchCancelCapture.onTouchEnd.onTouchEndCapture.onTouchMove.onTouchMoveCapture.onTouchStart.onTouchStartCapture.onPointerDown.onPointerDownCapture.onPointerMove.onPointerMoveCapture.onPointerUp.onPointerUpCapture.onPointerCancel.onPointerCancelCapture.onPointerEnter.onPointerEnterCapture.onPointerLeave.onPointerLeaveCapture.onPointerOver.onPointerOverCapture.onPointerOut.onPointerOutCapture.onGotPointerCapture.onGotPointerCaptureCapture.onLostPointerCapture.onLostPointerCaptureCapture.onScroll.onScrollCapture.onWheel.onWheelCapture.onAnimationStart.onAnimationStartCapture.onAnimationEnd.onAnimationEndCapture.onAnimationIteration.onAnimationIterationCapture.onTransitionEnd.onTransitionEndCapture".split(".");
function ee(e) {
	return typeof e == "string" && P.includes(e);
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesNoEvents.js
var te = /* @__PURE__ */ new Set(/* @__PURE__ */ "aria-activedescendant.aria-atomic.aria-autocomplete.aria-busy.aria-checked.aria-colcount.aria-colindex.aria-colspan.aria-controls.aria-current.aria-describedby.aria-details.aria-disabled.aria-errormessage.aria-expanded.aria-flowto.aria-haspopup.aria-hidden.aria-invalid.aria-keyshortcuts.aria-label.aria-labelledby.aria-level.aria-live.aria-modal.aria-multiline.aria-multiselectable.aria-orientation.aria-owns.aria-placeholder.aria-posinset.aria-pressed.aria-readonly.aria-relevant.aria-required.aria-roledescription.aria-rowcount.aria-rowindex.aria-rowspan.aria-selected.aria-setsize.aria-sort.aria-valuemax.aria-valuemin.aria-valuenow.aria-valuetext.className.color.height.id.lang.max.media.method.min.name.style.target.width.role.tabIndex.accentHeight.accumulate.additive.alignmentBaseline.allowReorder.alphabetic.amplitude.arabicForm.ascent.attributeName.attributeType.autoReverse.azimuth.baseFrequency.baselineShift.baseProfile.bbox.begin.bias.by.calcMode.capHeight.clip.clipPath.clipPathUnits.clipRule.colorInterpolation.colorInterpolationFilters.colorProfile.colorRendering.contentScriptType.contentStyleType.cursor.cx.cy.d.decelerate.descent.diffuseConstant.direction.display.divisor.dominantBaseline.dur.dx.dy.edgeMode.elevation.enableBackground.end.exponent.externalResourcesRequired.fill.fillOpacity.fillRule.filter.filterRes.filterUnits.floodColor.floodOpacity.focusable.fontFamily.fontSize.fontSizeAdjust.fontStretch.fontStyle.fontVariant.fontWeight.format.from.fx.fy.g1.g2.glyphName.glyphOrientationHorizontal.glyphOrientationVertical.glyphRef.gradientTransform.gradientUnits.hanging.horizAdvX.horizOriginX.href.ideographic.imageRendering.in2.in.intercept.k1.k2.k3.k4.k.kernelMatrix.kernelUnitLength.kerning.keyPoints.keySplines.keyTimes.lengthAdjust.letterSpacing.lightingColor.limitingConeAngle.local.markerEnd.markerHeight.markerMid.markerStart.markerUnits.markerWidth.mask.maskContentUnits.maskUnits.mathematical.mode.numOctaves.offset.opacity.operator.order.orient.orientation.origin.overflow.overlinePosition.overlineThickness.paintOrder.panose1.pathLength.patternContentUnits.patternTransform.patternUnits.pointerEvents.pointsAtX.pointsAtY.pointsAtZ.preserveAlpha.preserveAspectRatio.primitiveUnits.r.radius.refX.refY.renderingIntent.repeatCount.repeatDur.requiredExtensions.requiredFeatures.restart.result.rotate.rx.ry.seed.shapeRendering.slope.spacing.specularConstant.specularExponent.speed.spreadMethod.startOffset.stdDeviation.stemh.stemv.stitchTiles.stopColor.stopOpacity.strikethroughPosition.strikethroughThickness.string.stroke.strokeDasharray.strokeDashoffset.strokeLinecap.strokeLinejoin.strokeMiterlimit.strokeOpacity.strokeWidth.surfaceScale.systemLanguage.tableValues.targetX.targetY.textAnchor.textDecoration.textLength.textRendering.to.transform.u1.u2.underlinePosition.underlineThickness.unicode.unicodeBidi.unicodeRange.unitsPerEm.vAlphabetic.values.vectorEffect.version.vertAdvY.vertOriginX.vertOriginY.vHanging.vIdeographic.viewTarget.visibility.vMathematical.widths.wordSpacing.writingMode.x1.x2.x.xChannelSelector.xHeight.xlinkActuate.xlinkArcrole.xlinkHref.xlinkRole.xlinkShow.xlinkTitle.xlinkType.xmlBase.xmlLang.xmlns.xmlnsXlink.xmlSpace.y1.y2.y.yChannelSelector.z.zoomAndPan.ref.key.angle".split("."));
function ne(e) {
	return typeof e == "string" && te.has(e);
}
function re(e) {
	return typeof e == "string" && e.startsWith("data-");
}
function F(e) {
	if (typeof e != "object" || !e) return {};
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (ne(n) || re(n)) && (t[n] = e[n]);
	return t;
}
function ie(e) {
	if (e == null) return null;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && typeof e.props == "object" && e.props !== null) {
		var t = e.props;
		return F(t);
	}
	return typeof e == "object" && !Array.isArray(e) ? F(e) : null;
}
//#endregion
//#region node_modules/recharts/es6/util/svgPropertiesAndEvents.js
function ae(e) {
	var t = {};
	for (var n in e) Object.prototype.hasOwnProperty.call(e, n) && (ne(n) || re(n) || ee(n)) && (t[n] = e[n]);
	return t;
}
//#endregion
//#region node_modules/recharts/es6/container/Surface.js
var oe = [
	"children",
	"width",
	"height",
	"viewBox",
	"className",
	"style",
	"title",
	"desc"
];
function se() {
	return se = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, se.apply(null, arguments);
}
function ce(e, t) {
	if (e == null) return {};
	var n, r, i = le(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function le(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var ue = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.width, i = e.height, a = e.viewBox, o = e.className, s = e.style, c = e.title, l = e.desc, u = ce(e, oe), d = a || {
		width: r,
		height: i,
		x: 0,
		y: 0
	}, f = N("recharts-surface", o);
	return /*#__PURE__*/ C.createElement("svg", se({}, ae(u), {
		className: f,
		width: r,
		height: i,
		style: s,
		viewBox: `${d.x} ${d.y} ${d.width} ${d.height}`,
		ref: t
	}), /*#__PURE__*/ C.createElement("title", null, c), /*#__PURE__*/ C.createElement("desc", null, l), n);
}), de = ["children", "className"];
function fe() {
	return fe = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, fe.apply(null, arguments);
}
function pe(e, t) {
	if (e == null) return {};
	var n, r, i = me(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function me(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var he = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = e.children, r = e.className, i = pe(e, de), a = N("recharts-layer", r);
	return /*#__PURE__*/ C.createElement("g", fe({ className: a }, ae(i), { ref: t }), n);
}), ge = /*#__PURE__*/ (0, C.createContext)(null);
//#endregion
//#region node_modules/d3-shape/src/constant.js
function _e(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-path/src/path.js
var ve = Math.PI, ye = 2 * ve, be = 1e-6, xe = ye - be;
function Se(e) {
	this._ += e[0];
	for (let t = 1, n = e.length; t < n; ++t) this._ += arguments[t] + e[t];
}
function Ce(e) {
	let t = Math.floor(e);
	if (!(t >= 0)) throw Error(`invalid digits: ${e}`);
	if (t > 15) return Se;
	let n = 10 ** t;
	return function(e) {
		this._ += e[0];
		for (let t = 1, r = e.length; t < r; ++t) this._ += Math.round(arguments[t] * n) / n + e[t];
	};
}
var we = class {
	constructor(e) {
		this._x0 = this._y0 = this._x1 = this._y1 = null, this._ = "", this._append = e == null ? Se : Ce(e);
	}
	moveTo(e, t) {
		this._append`M${this._x0 = this._x1 = +e},${this._y0 = this._y1 = +t}`;
	}
	closePath() {
		this._x1 !== null && (this._x1 = this._x0, this._y1 = this._y0, this._append`Z`);
	}
	lineTo(e, t) {
		this._append`L${this._x1 = +e},${this._y1 = +t}`;
	}
	quadraticCurveTo(e, t, n, r) {
		this._append`Q${+e},${+t},${this._x1 = +n},${this._y1 = +r}`;
	}
	bezierCurveTo(e, t, n, r, i, a) {
		this._append`C${+e},${+t},${+n},${+r},${this._x1 = +i},${this._y1 = +a}`;
	}
	arcTo(e, t, n, r, i) {
		if (e = +e, t = +t, n = +n, r = +r, i = +i, i < 0) throw Error(`negative radius: ${i}`);
		let a = this._x1, o = this._y1, s = n - e, c = r - t, l = a - e, u = o - t, d = l * l + u * u;
		if (this._x1 === null) this._append`M${this._x1 = e},${this._y1 = t}`;
		else if (d > be) if (!(Math.abs(u * s - c * l) > be) || !i) this._append`L${this._x1 = e},${this._y1 = t}`;
		else {
			let f = n - a, p = r - o, m = s * s + c * c, h = f * f + p * p, g = Math.sqrt(m), _ = Math.sqrt(d), v = i * Math.tan((ve - Math.acos((m + d - h) / (2 * g * _))) / 2), y = v / _, b = v / g;
			Math.abs(y - 1) > be && this._append`L${e + y * l},${t + y * u}`, this._append`A${i},${i},0,0,${+(u * f > l * p)},${this._x1 = e + b * s},${this._y1 = t + b * c}`;
		}
	}
	arc(e, t, n, r, i, a) {
		if (e = +e, t = +t, n = +n, a = !!a, n < 0) throw Error(`negative radius: ${n}`);
		let o = n * Math.cos(r), s = n * Math.sin(r), c = e + o, l = t + s, u = 1 ^ a, d = a ? r - i : i - r;
		this._x1 === null ? this._append`M${c},${l}` : (Math.abs(this._x1 - c) > be || Math.abs(this._y1 - l) > be) && this._append`L${c},${l}`, n && (d < 0 && (d = d % ye + ye), d > xe ? this._append`A${n},${n},0,1,${u},${e - o},${t - s}A${n},${n},0,1,${u},${this._x1 = c},${this._y1 = l}` : d > be && this._append`A${n},${n},0,${+(d >= ve)},${u},${this._x1 = e + n * Math.cos(i)},${this._y1 = t + n * Math.sin(i)}`);
	}
	rect(e, t, n, r) {
		this._append`M${this._x0 = this._x1 = +e},${this._y0 = this._y1 = +t}h${n = +n}v${+r}h${-n}Z`;
	}
	toString() {
		return this._;
	}
};
function Te() {
	return new we();
}
Te.prototype = we.prototype;
//#endregion
//#region node_modules/d3-shape/src/path.js
function Ee(e) {
	let t = 3;
	return e.digits = function(n) {
		if (!arguments.length) return t;
		if (n == null) t = null;
		else {
			let e = Math.floor(n);
			if (!(e >= 0)) throw RangeError(`invalid digits: ${n}`);
			t = e;
		}
		return e;
	}, () => new we(t);
}
Array.prototype.slice;
function De(e) {
	return typeof e == "object" && "length" in e ? e : Array.from(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linear.js
function Oe(e) {
	this._context = e;
}
Oe.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._point = 0;
	},
	lineEnd: function() {
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1: this._point = 2;
			default:
				this._context.lineTo(e, t);
				break;
		}
	}
};
function ke(e) {
	return new Oe(e);
}
//#endregion
//#region node_modules/d3-shape/src/point.js
function Ae(e) {
	return e[0];
}
function je(e) {
	return e[1];
}
//#endregion
//#region node_modules/d3-shape/src/line.js
function Me(e, t) {
	var n = _e(!0), r = null, i = ke, a = null, o = Ee(s);
	e = typeof e == "function" ? e : e === void 0 ? Ae : _e(e), t = typeof t == "function" ? t : t === void 0 ? je : _e(t);
	function s(s) {
		var c, l = (s = De(s)).length, u, d = !1, f;
		for (r == null && (a = i(f = o())), c = 0; c <= l; ++c) !(c < l && n(u = s[c], c, s)) === d && ((d = !d) ? a.lineStart() : a.lineEnd()), d && a.point(+e(u, c, s), +t(u, c, s));
		if (f) return a = null, f + "" || null;
	}
	return s.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : _e(+t), s) : e;
	}, s.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : _e(+e), s) : t;
	}, s.defined = function(e) {
		return arguments.length ? (n = typeof e == "function" ? e : _e(!!e), s) : n;
	}, s.curve = function(e) {
		return arguments.length ? (i = e, r != null && (a = i(r)), s) : i;
	}, s.context = function(e) {
		return arguments.length ? (e == null ? r = a = null : a = i(r = e), s) : r;
	}, s;
}
//#endregion
//#region node_modules/d3-shape/src/area.js
function Ne(e, t, n) {
	var r = null, i = _e(!0), a = null, o = ke, s = null, c = Ee(l);
	e = typeof e == "function" ? e : e === void 0 ? Ae : _e(+e), t = typeof t == "function" ? t : _e(t === void 0 ? 0 : +t), n = typeof n == "function" ? n : n === void 0 ? je : _e(+n);
	function l(l) {
		var u, d, f, p = (l = De(l)).length, m, h = !1, g, _ = Array(p), v = Array(p);
		for (a == null && (s = o(g = c())), u = 0; u <= p; ++u) {
			if (!(u < p && i(m = l[u], u, l)) === h) if (h = !h) d = u, s.areaStart(), s.lineStart();
			else {
				for (s.lineEnd(), s.lineStart(), f = u - 1; f >= d; --f) s.point(_[f], v[f]);
				s.lineEnd(), s.areaEnd();
			}
			h && (_[u] = +e(m, u, l), v[u] = +t(m, u, l), s.point(r ? +r(m, u, l) : _[u], n ? +n(m, u, l) : v[u]));
		}
		if (g) return s = null, g + "" || null;
	}
	function u() {
		return Me().defined(i).curve(o).context(a);
	}
	return l.x = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : _e(+t), r = null, l) : e;
	}, l.x0 = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : _e(+t), l) : e;
	}, l.x1 = function(e) {
		return arguments.length ? (r = e == null ? null : typeof e == "function" ? e : _e(+e), l) : r;
	}, l.y = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : _e(+e), n = null, l) : t;
	}, l.y0 = function(e) {
		return arguments.length ? (t = typeof e == "function" ? e : _e(+e), l) : t;
	}, l.y1 = function(e) {
		return arguments.length ? (n = e == null ? null : typeof e == "function" ? e : _e(+e), l) : n;
	}, l.lineX0 = l.lineY0 = function() {
		return u().x(e).y(t);
	}, l.lineY1 = function() {
		return u().x(e).y(n);
	}, l.lineX1 = function() {
		return u().x(r).y(t);
	}, l.defined = function(e) {
		return arguments.length ? (i = typeof e == "function" ? e : _e(!!e), l) : i;
	}, l.curve = function(e) {
		return arguments.length ? (o = e, a != null && (s = o(a)), l) : o;
	}, l.context = function(e) {
		return arguments.length ? (e == null ? a = s = null : s = o(a = e), l) : a;
	}, l;
}
//#endregion
//#region node_modules/d3-shape/src/curve/bump.js
var Pe = class {
	constructor(e, t) {
		this._context = e, this._x = t;
	}
	areaStart() {
		this._line = 0;
	}
	areaEnd() {
		this._line = NaN;
	}
	lineStart() {
		this._point = 0;
	}
	lineEnd() {
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	}
	point(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1: this._point = 2;
			default:
				this._x ? this._context.bezierCurveTo(this._x0 = (this._x0 + e) / 2, this._y0, this._x0, t, e, t) : this._context.bezierCurveTo(this._x0, this._y0 = (this._y0 + t) / 2, e, this._y0, e, t);
				break;
		}
		this._x0 = e, this._y0 = t;
	}
};
function Fe(e) {
	return new Pe(e, !0);
}
function Ie(e) {
	return new Pe(e, !1);
}
//#endregion
//#region node_modules/d3-shape/src/noop.js
function Le() {}
//#endregion
//#region node_modules/d3-shape/src/curve/basis.js
function Re(e, t, n) {
	e._context.bezierCurveTo((2 * e._x0 + e._x1) / 3, (2 * e._y0 + e._y1) / 3, (e._x0 + 2 * e._x1) / 3, (e._y0 + 2 * e._y1) / 3, (e._x0 + 4 * e._x1 + t) / 6, (e._y0 + 4 * e._y1 + n) / 6);
}
function ze(e) {
	this._context = e;
}
ze.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x0 = this._x1 = this._y0 = this._y1 = NaN, this._point = 0;
	},
	lineEnd: function() {
		switch (this._point) {
			case 3: Re(this, this._x1, this._y1);
			case 2:
				this._context.lineTo(this._x1, this._y1);
				break;
		}
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1:
				this._point = 2;
				break;
			case 2: this._point = 3, this._context.lineTo((5 * this._x0 + this._x1) / 6, (5 * this._y0 + this._y1) / 6);
			default:
				Re(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function Be(e) {
	return new ze(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisClosed.js
function Ve(e) {
	this._context = e;
}
Ve.prototype = {
	areaStart: Le,
	areaEnd: Le,
	lineStart: function() {
		this._x0 = this._x1 = this._x2 = this._x3 = this._x4 = this._y0 = this._y1 = this._y2 = this._y3 = this._y4 = NaN, this._point = 0;
	},
	lineEnd: function() {
		switch (this._point) {
			case 1:
				this._context.moveTo(this._x2, this._y2), this._context.closePath();
				break;
			case 2:
				this._context.moveTo((this._x2 + 2 * this._x3) / 3, (this._y2 + 2 * this._y3) / 3), this._context.lineTo((this._x3 + 2 * this._x2) / 3, (this._y3 + 2 * this._y2) / 3), this._context.closePath();
				break;
			case 3:
				this.point(this._x2, this._y2), this.point(this._x3, this._y3), this.point(this._x4, this._y4);
				break;
		}
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._x2 = e, this._y2 = t;
				break;
			case 1:
				this._point = 2, this._x3 = e, this._y3 = t;
				break;
			case 2:
				this._point = 3, this._x4 = e, this._y4 = t, this._context.moveTo((this._x0 + 4 * this._x1 + e) / 6, (this._y0 + 4 * this._y1 + t) / 6);
				break;
			default:
				Re(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function He(e) {
	return new Ve(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/basisOpen.js
function Ue(e) {
	this._context = e;
}
Ue.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x0 = this._x1 = this._y0 = this._y1 = NaN, this._point = 0;
	},
	lineEnd: function() {
		(this._line || this._line !== 0 && this._point === 3) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1;
				break;
			case 1:
				this._point = 2;
				break;
			case 2:
				this._point = 3;
				var n = (this._x0 + 4 * this._x1 + e) / 6, r = (this._y0 + 4 * this._y1 + t) / 6;
				this._line ? this._context.lineTo(n, r) : this._context.moveTo(n, r);
				break;
			case 3: this._point = 4;
			default:
				Re(this, e, t);
				break;
		}
		this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t;
	}
};
function We(e) {
	return new Ue(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/linearClosed.js
function Ge(e) {
	this._context = e;
}
Ge.prototype = {
	areaStart: Le,
	areaEnd: Le,
	lineStart: function() {
		this._point = 0;
	},
	lineEnd: function() {
		this._point && this._context.closePath();
	},
	point: function(e, t) {
		e = +e, t = +t, this._point ? this._context.lineTo(e, t) : (this._point = 1, this._context.moveTo(e, t));
	}
};
function Ke(e) {
	return new Ge(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/monotone.js
function qe(e) {
	return e < 0 ? -1 : 1;
}
function Je(e, t, n) {
	var r = e._x1 - e._x0, i = t - e._x1, a = (e._y1 - e._y0) / (r || i < 0 && -0), o = (n - e._y1) / (i || r < 0 && -0), s = (a * i + o * r) / (r + i);
	return (qe(a) + qe(o)) * Math.min(Math.abs(a), Math.abs(o), .5 * Math.abs(s)) || 0;
}
function Ye(e, t) {
	var n = e._x1 - e._x0;
	return n ? (3 * (e._y1 - e._y0) / n - t) / 2 : t;
}
function Xe(e, t, n) {
	var r = e._x0, i = e._y0, a = e._x1, o = e._y1, s = (a - r) / 3;
	e._context.bezierCurveTo(r + s, i + s * t, a - s, o - s * n, a, o);
}
function Ze(e) {
	this._context = e;
}
Ze.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x0 = this._x1 = this._y0 = this._y1 = this._t0 = NaN, this._point = 0;
	},
	lineEnd: function() {
		switch (this._point) {
			case 2:
				this._context.lineTo(this._x1, this._y1);
				break;
			case 3:
				Xe(this, this._t0, Ye(this, this._t0));
				break;
		}
		(this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line = 1 - this._line;
	},
	point: function(e, t) {
		var n = NaN;
		if (e = +e, t = +t, !(e === this._x1 && t === this._y1)) {
			switch (this._point) {
				case 0:
					this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
					break;
				case 1:
					this._point = 2;
					break;
				case 2:
					this._point = 3, Xe(this, Ye(this, n = Je(this, e, t)), n);
					break;
				default:
					Xe(this, this._t0, n = Je(this, e, t));
					break;
			}
			this._x0 = this._x1, this._x1 = e, this._y0 = this._y1, this._y1 = t, this._t0 = n;
		}
	}
};
function Qe(e) {
	this._context = new $e(e);
}
(Qe.prototype = Object.create(Ze.prototype)).point = function(e, t) {
	Ze.prototype.point.call(this, t, e);
};
function $e(e) {
	this._context = e;
}
$e.prototype = {
	moveTo: function(e, t) {
		this._context.moveTo(t, e);
	},
	closePath: function() {
		this._context.closePath();
	},
	lineTo: function(e, t) {
		this._context.lineTo(t, e);
	},
	bezierCurveTo: function(e, t, n, r, i, a) {
		this._context.bezierCurveTo(t, e, r, n, a, i);
	}
};
function et(e) {
	return new Ze(e);
}
function tt(e) {
	return new Qe(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/natural.js
function nt(e) {
	this._context = e;
}
nt.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x = [], this._y = [];
	},
	lineEnd: function() {
		var e = this._x, t = this._y, n = e.length;
		if (n) if (this._line ? this._context.lineTo(e[0], t[0]) : this._context.moveTo(e[0], t[0]), n === 2) this._context.lineTo(e[1], t[1]);
		else for (var r = rt(e), i = rt(t), a = 0, o = 1; o < n; ++a, ++o) this._context.bezierCurveTo(r[0][a], i[0][a], r[1][a], i[1][a], e[o], t[o]);
		(this._line || this._line !== 0 && n === 1) && this._context.closePath(), this._line = 1 - this._line, this._x = this._y = null;
	},
	point: function(e, t) {
		this._x.push(+e), this._y.push(+t);
	}
};
function rt(e) {
	var t, n = e.length - 1, r, i = Array(n), a = Array(n), o = Array(n);
	for (i[0] = 0, a[0] = 2, o[0] = e[0] + 2 * e[1], t = 1; t < n - 1; ++t) i[t] = 1, a[t] = 4, o[t] = 4 * e[t] + 2 * e[t + 1];
	for (i[n - 1] = 2, a[n - 1] = 7, o[n - 1] = 8 * e[n - 1] + e[n], t = 1; t < n; ++t) r = i[t] / a[t - 1], a[t] -= r, o[t] -= r * o[t - 1];
	for (i[n - 1] = o[n - 1] / a[n - 1], t = n - 2; t >= 0; --t) i[t] = (o[t] - i[t + 1]) / a[t];
	for (a[n - 1] = (e[n] + i[n - 1]) / 2, t = 0; t < n - 1; ++t) a[t] = 2 * e[t + 1] - i[t + 1];
	return [i, a];
}
function it(e) {
	return new nt(e);
}
//#endregion
//#region node_modules/d3-shape/src/curve/step.js
function at(e, t) {
	this._context = e, this._t = t;
}
at.prototype = {
	areaStart: function() {
		this._line = 0;
	},
	areaEnd: function() {
		this._line = NaN;
	},
	lineStart: function() {
		this._x = this._y = NaN, this._point = 0;
	},
	lineEnd: function() {
		0 < this._t && this._t < 1 && this._point === 2 && this._context.lineTo(this._x, this._y), (this._line || this._line !== 0 && this._point === 1) && this._context.closePath(), this._line >= 0 && (this._t = 1 - this._t, this._line = 1 - this._line);
	},
	point: function(e, t) {
		switch (e = +e, t = +t, this._point) {
			case 0:
				this._point = 1, this._line ? this._context.lineTo(e, t) : this._context.moveTo(e, t);
				break;
			case 1: this._point = 2;
			default:
				if (this._t <= 0) this._context.lineTo(this._x, t), this._context.lineTo(e, t);
				else {
					var n = this._x * (1 - this._t) + e * this._t;
					this._context.lineTo(n, this._y), this._context.lineTo(n, t);
				}
				break;
		}
		this._x = e, this._y = t;
	}
};
function ot(e) {
	return new at(e, .5);
}
function st(e) {
	return new at(e, 0);
}
function ct(e) {
	return new at(e, 1);
}
//#endregion
//#region node_modules/d3-shape/src/offset/none.js
function lt(e, t) {
	if ((o = e.length) > 1) for (var n = 1, r, i, a = e[t[0]], o, s = a.length; n < o; ++n) for (i = a, a = e[t[n]], r = 0; r < s; ++r) a[r][1] += a[r][0] = isNaN(i[r][1]) ? i[r][0] : i[r][1];
}
//#endregion
//#region node_modules/d3-shape/src/order/none.js
function ut(e) {
	for (var t = e.length, n = Array(t); --t >= 0;) n[t] = t;
	return n;
}
//#endregion
//#region node_modules/d3-shape/src/stack.js
function dt(e, t) {
	return e[t];
}
function ft(e) {
	let t = [];
	return t.key = e, t;
}
function pt() {
	var e = _e([]), t = ut, n = lt, r = dt;
	function i(i) {
		var a = Array.from(e.apply(this, arguments), ft), o, s = a.length, c = -1, l;
		for (let e of i) for (o = 0, ++c; o < s; ++o) (a[o][c] = [0, +r(e, a[o].key, c, i)]).data = e;
		for (o = 0, l = De(t(a)); o < s; ++o) a[l[o]].index = o;
		return n(a, l), a;
	}
	return i.keys = function(t) {
		return arguments.length ? (e = typeof t == "function" ? t : _e(Array.from(t)), i) : e;
	}, i.value = function(e) {
		return arguments.length ? (r = typeof e == "function" ? e : _e(+e), i) : r;
	}, i.order = function(e) {
		return arguments.length ? (t = e == null ? ut : typeof e == "function" ? e : _e(Array.from(e)), i) : t;
	}, i.offset = function(e) {
		return arguments.length ? (n = e == null ? lt : e, i) : n;
	}, i;
}
//#endregion
//#region node_modules/d3-shape/src/offset/expand.js
function mt(e, t) {
	if ((r = e.length) > 0) {
		for (var n, r, i = 0, a = e[0].length, o; i < a; ++i) {
			for (o = n = 0; n < r; ++n) o += e[n][i][1] || 0;
			if (o) for (n = 0; n < r; ++n) e[n][i][1] /= o;
		}
		lt(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/silhouette.js
function ht(e, t) {
	if ((i = e.length) > 0) {
		for (var n = 0, r = e[t[0]], i, a = r.length; n < a; ++n) {
			for (var o = 0, s = 0; o < i; ++o) s += e[o][n][1] || 0;
			r[n][1] += r[n][0] = -s / 2;
		}
		lt(e, t);
	}
}
//#endregion
//#region node_modules/d3-shape/src/offset/wiggle.js
function gt(e, t) {
	if (!(!((o = e.length) > 0) || !((a = (i = e[t[0]]).length) > 0))) {
		for (var n = 0, r = 1, i, a, o; r < a; ++r) {
			for (var s = 0, c = 0, l = 0; s < o; ++s) {
				for (var u = e[t[s]], d = u[r][1] || 0, f = (d - (u[r - 1][1] || 0)) / 2, p = 0; p < s; ++p) {
					var m = e[t[p]], h = m[r][1] || 0, g = m[r - 1][1] || 0;
					f += h - g;
				}
				c += d, l += f * d;
			}
			i[r - 1][1] += i[r - 1][0] = n, c && (n -= l / c);
		}
		i[r - 1][1] += i[r - 1][0] = n, lt(e, t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isUnsafeProperty.mjs
function _t(e) {
	return e === "__proto__";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isDeepKey.mjs
function vt(e) {
	switch (typeof e) {
		case "number":
		case "symbol": return !1;
		case "string": return e.includes(".") || e.includes("[") || e.includes("]");
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/toKey.mjs
function yt(e) {
	var t;
	return typeof e == "string" || typeof e == "symbol" ? e : Object.is(e == null || (t = e.valueOf) == null ? void 0 : t.call(e), -0) ? "-0" : String(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toString.mjs
function bt(e) {
	if (e == null) return "";
	if (typeof e == "string") return e;
	if (Array.isArray(e)) return e.map(bt).join(",");
	let t = String(e);
	return t === "0" && Object.is(Number(e), -0) ? "-0" : t;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toPath.mjs
function xt(e) {
	if (Array.isArray(e)) return e.map(yt);
	if (typeof e == "symbol") return [e];
	e = bt(e);
	let t = [], n = e.length;
	if (n === 0) return t;
	let r = 0, i = "", a = "", o = !1;
	for (e.charCodeAt(0) === 46 && t.push(""); r < n;) {
		let s = e[r];
		if (a) s === "\\" && r + 1 < n ? (r++, i += e[r]) : s === a ? a = "" : i += s;
		else if (o) s === "\"" || s === "'" ? a = s : s === "]" ? (o = !1, t.push(i), i = "") : i += s;
		else if (s === "[") o = !0, i && (t.push(i), i = "");
		else if (s === ".") {
			i && (t.push(i), i = "");
			let n = e[r + 1];
			(n === void 0 || n === ".") && t.push("");
		} else i += s;
		r++;
	}
	return i && t.push(i), t;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/get.mjs
function St(e, t, n) {
	if (e == null) return n;
	switch (typeof t) {
		case "string": {
			if (_t(t)) return n;
			let r = e[t];
			return r === void 0 ? vt(t) && !Object.hasOwn(e, t) ? St(e, xt(t), n) : n : r;
		}
		case "number":
		case "symbol": {
			typeof t == "number" && (t = yt(t));
			let r = e[t];
			return r === void 0 ? n : r;
		}
		default: {
			if (Array.isArray(t)) return Ct(e, t, n);
			if (t = Object.is(t == null ? void 0 : t.valueOf(), -0) ? "-0" : String(t), _t(t)) return n;
			let r = e[t];
			return r === void 0 ? n : r;
		}
	}
}
function Ct(e, t, n) {
	if (t.length === 0) return n;
	let r = e;
	for (let e = 0; e < t.length; e++) {
		if (r == null || _t(t[e])) return n;
		r = r[t[e]];
	}
	return r === void 0 ? n : r;
}
//#endregion
//#region node_modules/recharts/es6/util/round.js
var wt = 4;
function Tt(e) {
	var t = 10 ** (arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : wt), n = Math.round(e * t) / t;
	return Object.is(n, -0) ? 0 : n;
}
function Et(e) {
	var t = [...arguments].slice(1);
	return e.reduce((e, n, r) => {
		var i = t[r - 1];
		return typeof i == "string" ? e + i + n : i === void 0 ? e + n : e + Tt(i) + n;
	}, "");
}
//#endregion
//#region node_modules/recharts/es6/util/DataUtils.js
var Dt = (e) => e === 0 ? 0 : e > 0 ? 1 : -1, Ot = (e) => typeof e == "number" && e != +e, kt = (e) => typeof e == "string" && e.length > 1 && e.indexOf("%") === e.length - 1, I = (e) => (typeof e == "number" || e instanceof Number) && !Ot(e), At = (e) => I(e) || typeof e == "string", jt = 0, Mt = (e) => {
	var t = ++jt;
	return `${e || ""}${t}`;
}, Nt = function(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : 0, r = arguments.length > 3 && arguments[3] !== void 0 && arguments[3];
	if (!I(e) && typeof e != "string") return n;
	var i;
	if (kt(e)) {
		if (t == null) return n;
		var a = e.indexOf("%");
		i = t * parseFloat(e.slice(0, a)) / 100;
	} else i = +e;
	return Ot(i) && (i = n), r && t != null && i > t && (i = t), i;
}, Pt = (e) => {
	if (!Array.isArray(e)) return !1;
	for (var t = e.length, n = {}, r = 0; r < t; r++) if (!n[String(e[r])]) n[String(e[r])] = !0;
	else return !0;
	return !1;
};
function Ft(e, t, n) {
	return I(e) && I(t) ? Tt(e + n * (t - e)) : t;
}
function It(e, t, n) {
	if (!(!e || !e.length)) return e.find((e) => e && (typeof t == "function" ? t(e) : St(e, t)) === n);
}
var Lt = (e) => e == null, Rt = (e) => Lt(e) ? e : `${e.charAt(0).toUpperCase()}${e.slice(1)}`;
function zt(e) {
	return e != null;
}
function Bt() {}
//#endregion
//#region node_modules/recharts/es6/util/types.js
var Vt = (e) => "radius" in e && "startAngle" in e && "endAngle" in e, Ht = (e, t) => {
	if (!e || typeof e == "function" || typeof e == "boolean") return null;
	var n = e;
	if (/*#__PURE__*/ (0, C.isValidElement)(e) && (n = e.props), typeof n != "object" && typeof n != "function") return null;
	var r = {};
	return Object.keys(n).forEach((e) => {
		ee(e) && typeof n[e] == "function" && (r[e] = t || ((t) => n[e](n, t)));
	}), r;
}, Ut = (e, t, n) => (r) => (e(t, n, r), null), Wt = (e, t, n) => {
	if (e === null || typeof e != "object" && typeof e != "function") return null;
	var r = null;
	return Object.keys(e).forEach((i) => {
		var a = e[i];
		ee(i) && typeof a == "function" && (r || (r = {}), r[i] = Ut(a, t, n));
	}), r;
};
//#endregion
//#region node_modules/recharts/es6/util/resolveDefaultProps.js
function L(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Gt(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? L(Object(n), !0).forEach(function(t) {
			Kt(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : L(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Kt(e, t, n) {
	return (t = qt(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function qt(e) {
	var t = Jt(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Jt(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Yt(e, t) {
	var n = Gt({}, e), r = t;
	return Object.keys(t).reduce((e, t) => (e[t] === void 0 && r[t] !== void 0 && (e[t] = r[t]), e), n);
}
//#endregion
//#region node_modules/es-toolkit/dist/array/uniqBy.mjs
function Xt(e, t) {
	let n = /* @__PURE__ */ new Map();
	for (let r = 0; r < e.length; r++) {
		let i = e[r], a = t(i, r, e);
		n.has(a) || n.set(a, i);
	}
	return Array.from(n.values());
}
//#endregion
//#region node_modules/es-toolkit/dist/function/ary.mjs
function Zt(e, t) {
	return function(...n) {
		return e.apply(this, n.slice(0, t));
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/function/identity.mjs
function Qt(e) {
	return e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/property.mjs
function $t(e) {
	return function(t) {
		return St(t, e);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isPrimitive.mjs
function en(e) {
	return e == null || typeof e != "object" && typeof e != "function";
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isTypedArray.mjs
function tn(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getSymbols.mjs
function nn(e) {
	return Object.getOwnPropertySymbols(e).filter((t) => Object.prototype.propertyIsEnumerable.call(e, t));
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/getTag.mjs
function rn(e) {
	return e == null ? e === void 0 ? "[object Undefined]" : "[object Null]" : Object.prototype.toString.call(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/tags.mjs
var an = "[object RegExp]", on = "[object String]", sn = "[object Number]", cn = "[object Boolean]", ln = "[object Arguments]", un = "[object Symbol]", dn = "[object Date]", fn = "[object Map]", pn = "[object Set]", mn = "[object Array]", hn = "[object ArrayBuffer]", gn = "[object Object]", _n = "[object DataView]", vn = "[object Uint8Array]", yn = "[object Uint8ClampedArray]", bn = "[object Uint16Array]", xn = "[object Uint32Array]", Sn = "[object Int8Array]", Cn = "[object Int16Array]", wn = "[object Int32Array]", Tn = "[object Float32Array]", En = "[object Float64Array]", Dn = typeof globalThis == "object" && globalThis || typeof window == "object" && window || typeof self == "object" && self || typeof global == "object" && global || (function() {
	return this;
})();
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isBuffer.mjs
function On(e) {
	return Dn.Buffer !== void 0 && Dn.Buffer.isBuffer(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeepWith.mjs
function kn(e, t) {
	return An(e, void 0, e, /* @__PURE__ */ new Map(), t);
}
function An(e, t, n, r = /* @__PURE__ */ new Map(), i = void 0) {
	let a = i == null ? void 0 : i(e, t, n, r);
	if (a !== void 0) return a;
	if (en(e)) return e;
	if (r.has(e)) return r.get(e);
	if (Array.isArray(e)) {
		let t = Array(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = An(e[a], a, n, r, i);
		return Object.hasOwn(e, "index") && (t.index = e.index), Object.hasOwn(e, "input") && (t.input = e.input), t;
	}
	if (e instanceof Date) return new Date(e.getTime());
	if (e instanceof RegExp) {
		let t = new RegExp(e.source, e.flags);
		return t.lastIndex = e.lastIndex, t;
	}
	if (e instanceof Map) {
		let t = /* @__PURE__ */ new Map();
		r.set(e, t);
		for (let [a, o] of e) t.set(a, An(o, a, n, r, i));
		return t;
	}
	if (e instanceof Set) {
		let t = /* @__PURE__ */ new Set();
		r.set(e, t);
		for (let a of e) t.add(An(a, void 0, n, r, i));
		return t;
	}
	if (On(e)) return e.subarray();
	if (tn(e)) {
		let t = new (Object.getPrototypeOf(e)).constructor(e.length);
		r.set(e, t);
		for (let a = 0; a < e.length; a++) t[a] = An(e[a], a, n, r, i);
		return t;
	}
	if (e instanceof ArrayBuffer || typeof SharedArrayBuffer < "u" && e instanceof SharedArrayBuffer) return e.slice(0);
	if (e instanceof DataView) {
		let t = new DataView(e.buffer.slice(0), e.byteOffset, e.byteLength);
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	if (typeof File < "u" && e instanceof File) {
		let t = new File([e], e.name, { type: e.type });
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	if (typeof Blob < "u" && e instanceof Blob) {
		let t = new Blob([e], { type: e.type });
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	if (e instanceof Error) {
		let t = structuredClone(e);
		return r.set(e, t), t.message = e.message, t.name = e.name, t.stack = e.stack, t.cause = e.cause, t.constructor = e.constructor, jn(t, e, n, r, i), t;
	}
	if (e instanceof Boolean) {
		let t = new Boolean(e.valueOf());
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	if (e instanceof Number) {
		let t = new Number(e.valueOf());
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	if (e instanceof String) {
		let t = new String(e.valueOf());
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	if (typeof e == "object" && Mn(e)) {
		let t = Object.create(Object.getPrototypeOf(e));
		return r.set(e, t), jn(t, e, n, r, i), t;
	}
	return e;
}
function jn(e, t, n = e, r, i) {
	let a = [...Object.keys(t), ...nn(t)];
	for (let o = 0; o < a.length; o++) {
		let s = a[o], c = Object.getOwnPropertyDescriptor(e, s);
		(c == null || c.writable) && (e[s] = An(t[s], s, n, r, i));
	}
}
function Mn(e) {
	switch (rn(e)) {
		case ln:
		case mn:
		case hn:
		case _n:
		case cn:
		case dn:
		case Tn:
		case En:
		case Sn:
		case Cn:
		case wn:
		case fn:
		case sn:
		case gn:
		case an:
		case pn:
		case on:
		case un:
		case vn:
		case yn:
		case bn:
		case xn: return !0;
		default: return !1;
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/object/cloneDeep.mjs
function Nn(e) {
	return An(e, void 0, e, /* @__PURE__ */ new Map(), void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/_internal/isEqualsSameValueZero.mjs
function Pn(e, t) {
	return e === t || Number.isNaN(e) && Number.isNaN(t);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObject.mjs
function Fn(e) {
	return e !== null && (typeof e == "object" || typeof e == "function");
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatchWith.mjs
function In(e, t, n) {
	return typeof n == "function" ? Ln(e, t, function e(t, r, i, a, o, s) {
		let c = n(t, r, i, a, o, s);
		return c === void 0 ? Ln(t, r, e, s, !1) : !!c;
	}, /* @__PURE__ */ new Map(), !0) : In(e, t, () => void 0);
}
function Ln(e, t, n, r, i = !1) {
	if (t === e) return !0;
	switch (typeof t) {
		case "object": return Rn(e, t, n, r);
		case "function": return Object.keys(t).length > 0 ? Ln(e, { ...t }, n, r, i) : Pn(e, t);
		default: return Fn(e) && i ? typeof t != "string" || t === "" : Pn(e, t);
	}
}
function Rn(e, t, n, r) {
	if (t == null) return !0;
	if (Array.isArray(t)) return Bn(e, t, n, r);
	if (t instanceof Map) return zn(e, t, n, r);
	if (t instanceof Set) return Vn(e, t, n, r);
	let i = Object.keys(t);
	if (e == null || en(e)) return i.length === 0;
	if (i.length === 0) return !0;
	if (r != null && r.has(t)) return r.get(t) === e;
	r == null || r.set(t, e);
	try {
		for (let a = 0; a < i.length; a++) {
			let o = i[a];
			if (!en(e) && !(o in e) || t[o] === void 0 && e[o] !== void 0 || t[o] === null && e[o] !== null || !n(e[o], t[o], o, e, t, r)) return !1;
		}
		return !0;
	} finally {
		r == null || r.delete(t);
	}
}
function zn(e, t, n, r) {
	if (t.size === 0) return !0;
	if (!(e instanceof Map)) return !1;
	for (let [i, a] of t.entries()) if (n(e.get(i), a, i, e, t, r) === !1) return !1;
	return !0;
}
function Bn(e, t, n, r) {
	if (t.length === 0) return !0;
	if (!Array.isArray(e)) return !1;
	let i = /* @__PURE__ */ new Set();
	for (let a = 0; a < t.length; a++) {
		let o = t[a], s = !1;
		for (let c = 0; c < e.length; c++) {
			if (i.has(c)) continue;
			let l = e[c], u = !1;
			if (n(l, o, a, e, t, r) && (u = !0), u) {
				i.add(c), s = !0;
				break;
			}
		}
		if (!s) return !1;
	}
	return !0;
}
function Vn(e, t, n, r) {
	return t.size === 0 || e instanceof Set && Bn([...e], [...t], n, r);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isMatch.mjs
function Hn(e, t) {
	return In(e, t, () => void 0);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matches.mjs
function Un(e) {
	return e = Nn(e), (t) => Hn(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeepWith.mjs
function Wn(e, t) {
	return kn(e, (n, r, i, a) => {
		let o = t == null ? void 0 : t(n, r, i, a);
		if (o !== void 0) return o;
		if (typeof e == "object") {
			if (rn(e) === "[object Object]" && typeof e.constructor != "function") {
				let t = {};
				return a.set(e, t), jn(t, e, i, a), t;
			}
			switch (Object.prototype.toString.call(e)) {
				case sn:
				case on:
				case cn: {
					let t = new e.constructor(e == null ? void 0 : e.valueOf());
					return jn(t, e), t;
				}
				case ln: {
					let t = {};
					return jn(t, e), t.length = e.length, t[Symbol.iterator] = e[Symbol.iterator], t;
				}
				default: return;
			}
		}
	});
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/cloneDeep.mjs
function Gn(e) {
	return Wn(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isIndex.mjs
var Kn = /^(?:0|[1-9]\d*)$/;
function qn(e, t = 2 ** 53 - 1) {
	switch (typeof e) {
		case "number": return Number.isInteger(e) && e >= 0 && e < t;
		case "symbol": return !1;
		case "string": return Kn.test(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArguments.mjs
function Jn(e) {
	return typeof e == "object" && !!e && rn(e) === "[object Arguments]";
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/object/has.mjs
function Yn(e, t) {
	let n;
	if (n = Array.isArray(t) ? t : typeof t == "string" && vt(t) && (e == null ? void 0 : e[t]) == null ? xt(t) : [t], n.length === 0) return !1;
	let r = e;
	for (let e = 0; e < n.length; e++) {
		let t = n[e];
		if ((r == null || !Object.hasOwn(r, t)) && !((Array.isArray(r) || Jn(r)) && qn(t) && t < r.length)) return !1;
		r = r[t];
	}
	return !0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/matchesProperty.mjs
function Xn(e, t) {
	switch (typeof e) {
		case "object":
			Object.is(e == null ? void 0 : e.valueOf(), -0) && (e = "-0");
			break;
		case "number":
			e = yt(e);
			break;
	}
	return t = Gn(t), function(n) {
		let r = St(n, e);
		return r === void 0 ? Yn(n, e) : t === void 0 ? r === void 0 : Hn(r, t);
	};
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/iteratee.mjs
function Zn(e) {
	if (e == null) return Qt;
	switch (typeof e) {
		case "function": return e;
		case "object": return Array.isArray(e) && e.length === 2 ? Xn(e[0], e[1]) : Un(e);
		case "string":
		case "symbol":
		case "number": return $t(e);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/predicate/isLength.mjs
function Qn(e) {
	return Number.isSafeInteger(e) && e >= 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLike.mjs
function $n(e) {
	return e != null && typeof e != "function" && Qn(e.length);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isObjectLike.mjs
function er(e) {
	return typeof e == "object" && !!e;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isArrayLikeObject.mjs
function tr(e) {
	return er(e) && $n(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/uniqBy.mjs
function nr(e, t = Qt) {
	return tr(e) ? Xt(Array.from(e), Zt(Zn(t), 1)) : [];
}
//#endregion
//#region node_modules/recharts/es6/util/payload/getUniqPayload.js
function rr(e, t, n) {
	return t === !0 ? nr(e, n) : typeof t == "function" ? nr(e, t) : e;
}
//#endregion
//#region node_modules/use-sync-external-store/cjs/use-sync-external-store-shim.production.js
var ir = /* @__PURE__ */ o(((e) => {
	var t = d();
	function n(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var r = typeof Object.is == "function" ? Object.is : n, i = t.useState, a = t.useEffect, o = t.useLayoutEffect, s = t.useDebugValue;
	function c(e, t) {
		var n = t(), r = i({ inst: {
			value: n,
			getSnapshot: t
		} }), c = r[0].inst, u = r[1];
		return o(function() {
			c.value = n, c.getSnapshot = t, l(c) && u({ inst: c });
		}, [
			e,
			n,
			t
		]), a(function() {
			return l(c) && u({ inst: c }), e(function() {
				l(c) && u({ inst: c });
			});
		}, [e]), s(n), n;
	}
	function l(e) {
		var t = e.getSnapshot;
		e = e.value;
		try {
			var n = t();
			return !r(e, n);
		} catch (e) {
			return !0;
		}
	}
	function u(e, t) {
		return t();
	}
	var f = typeof window > "u" || window.document === void 0 || window.document.createElement === void 0 ? u : c;
	e.useSyncExternalStore = t.useSyncExternalStore === void 0 ? f : t.useSyncExternalStore;
})), ar = /* @__PURE__ */ o(((e, t) => {
	t.exports = ir();
})), or = /* @__PURE__ */ o(((e) => {
	var t = d(), n = ar();
	function r(e, t) {
		return e === t && (e !== 0 || 1 / e == 1 / t) || e !== e && t !== t;
	}
	var i = typeof Object.is == "function" ? Object.is : r, a = n.useSyncExternalStore, o = t.useRef, s = t.useEffect, c = t.useMemo, l = t.useDebugValue;
	e.useSyncExternalStoreWithSelector = function(e, t, n, r, u) {
		var d = o(null);
		if (d.current === null) {
			var f = {
				hasValue: !1,
				value: null
			};
			d.current = f;
		} else f = d.current;
		d = c(function() {
			function e(e) {
				if (!a) {
					if (a = !0, o = e, e = r(e), u !== void 0 && f.hasValue) {
						var t = f.value;
						if (u(t, e)) return s = t;
					}
					return s = e;
				}
				if (t = s, i(o, e)) return t;
				var n = r(e);
				return u !== void 0 && u(t, n) ? (o = e, t) : (o = e, s = n);
			}
			var a = !1, o, s, c = n === void 0 ? null : n;
			return [function() {
				return e(t());
			}, c === null ? void 0 : function() {
				return e(c());
			}];
		}, [
			t,
			n,
			r,
			u
		]);
		var p = a(e, d[0], d[1]);
		return s(function() {
			f.hasValue = !0, f.value = p;
		}, [p]), l(p), p;
	};
})), sr = /* @__PURE__ */ o(((e, t) => {
	t.exports = or();
})), cr = /*#__PURE__*/ (0, C.createContext)(null), lr = sr(), ur = (e) => e, R = () => {
	var e = (0, C.useContext)(cr);
	return e ? e.store.dispatch : ur;
}, dr = () => {}, fr = () => dr, pr = (e, t) => e === t;
function z(e) {
	var t = (0, C.useContext)(cr), n = (0, C.useMemo)(() => t ? (t) => {
		if (t != null) return e(t);
	} : dr, [t, e]);
	return (0, lr.useSyncExternalStoreWithSelector)(t ? t.subscription.addNestedSub : fr, t ? t.store.getState : dr, t ? t.store.getState : dr, n, pr);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/typeof.js
function mr(e) {
	"@babel/helpers - typeof";
	return mr = typeof Symbol == "function" && typeof Symbol.iterator == "symbol" ? function(e) {
		return typeof e;
	} : function(e) {
		return e && typeof Symbol == "function" && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e;
	}, mr(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPrimitive.js
function hr(e, t) {
	if (mr(e) != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (mr(r) != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/toPropertyKey.js
function gr(e) {
	var t = hr(e, "string");
	return mr(t) == "symbol" ? t : t + "";
}
//#endregion
//#region \0@oxc-project+runtime@0.139.0/helpers/esm/defineProperty.js
function _r(e, t, n) {
	return (t = gr(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
//#endregion
//#region node_modules/reselect/dist/reselect.mjs
function vr(e, t = `expected a function, instead received ${typeof e}`) {
	if (typeof e != "function") throw TypeError(t);
}
function yr(e, t = "expected all items to be functions, instead received the following types: ") {
	if (!e.every((e) => typeof e == "function")) {
		let n = e.map((e) => typeof e == "function" ? `function ${e.name || "unnamed"}()` : typeof e).join(", ");
		throw TypeError(`${t}[${n}]`);
	}
}
var br = (e) => Array.isArray(e) ? e : [e];
function xr(e) {
	let t = Array.isArray(e[0]) ? e[0] : e;
	return yr(t, "createSelector expects all input-selectors to be functions, but received the following types: "), t;
}
function Sr(e, t) {
	let n = [], { length: r } = e;
	for (let i = 0; i < r; i++) n.push(e[i].apply(null, t));
	return n;
}
var Cr = class {
	constructor(e) {
		this.value = e;
	}
	deref() {
		return this.value;
	}
}, wr = typeof WeakRef > "u" ? Cr : WeakRef, Tr = 0, Er = 1;
function Dr() {
	return {
		s: Tr,
		v: void 0,
		o: null,
		p: null
	};
}
function Or(e) {
	return e instanceof wr ? e.deref() : e;
}
function kr(e, t = {}) {
	let n = Dr(), { resultEqualityCheck: r } = t, i, a = 0;
	function o() {
		let t = n, { length: o } = arguments;
		for (let e = 0, n = o; e < n; e++) {
			let n = arguments[e];
			if (typeof n == "function" || typeof n == "object" && n) {
				let e = t.o;
				e === null && (t.o = e = /* @__PURE__ */ new WeakMap());
				let r = e.get(n);
				r === void 0 ? (t = Dr(), e.set(n, t)) : t = r;
			} else {
				let e = t.p;
				e === null && (t.p = e = /* @__PURE__ */ new Map());
				let r = e.get(n);
				r === void 0 ? (t = Dr(), e.set(n, t)) : t = r;
			}
		}
		let s = t, c;
		if (t.s === Er) c = t.v;
		else if (c = e.apply(null, arguments), a++, r) {
			let e = Or(i);
			e != null && r(e, c) && (c = e, a !== 0 && a--), i = typeof c == "object" && c || typeof c == "function" ? /* @__PURE__ */ new wr(c) : c;
		}
		return s.s = Er, s.v = c, c;
	}
	return o.clearCache = () => {
		n = Dr(), o.resetResultsCount();
	}, o.resultsCount = () => a, o.resetResultsCount = () => {
		a = 0;
	}, o;
}
function Ar(e, ...t) {
	let n = typeof e == "function" ? {
		memoize: e,
		memoizeOptions: t
	} : e, r = (...e) => {
		let t = 0, r = 0, i, a = {}, o = e.pop();
		typeof o == "object" && (a = o, o = e.pop()), vr(o, `createSelector expects an output function after the inputs, but received: [${typeof o}]`);
		let { memoize: s, memoizeOptions: c = [], argsMemoize: l = kr, argsMemoizeOptions: u = [] } = {
			...n,
			...a
		}, d = br(c), f = br(u), p = xr(e), m = s(function() {
			return t++, o.apply(null, arguments);
		}, ...d), h = l(function() {
			r++;
			let e = Sr(p, arguments);
			return i = m.apply(null, e), i;
		}, ...f);
		return Object.assign(h, {
			resultFunc: o,
			memoizedResultFunc: m,
			dependencies: p,
			dependencyRecomputations: () => r,
			resetDependencyRecomputations: () => {
				r = 0;
			},
			lastResult: () => i,
			recomputations: () => t,
			resetRecomputations: () => {
				t = 0;
			},
			memoize: s,
			argsMemoize: l
		});
	};
	return Object.assign(r, { withTypes: () => r }), r;
}
var B = /* @__PURE__ */ Ar(kr);
//#endregion
//#region node_modules/es-toolkit/dist/array/flatten.mjs
function jr(e, t = 1) {
	let n = [], r = Math.floor(t), i = (e, t) => {
		for (let a = 0; a < e.length; a++) {
			let o = e[a];
			Array.isArray(o) && t < r ? i(o, t + 1) : n.push(o);
		}
	};
	return i(e, 0), n;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isIterateeCall.mjs
function Mr(e, t, n) {
	return Fn(n) && (typeof t == "number" && $n(n) && qn(t) && t < n.length || typeof t == "string" && t in n) ? Pn(n[t], e) : !1;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/compareValues.mjs
function Nr(e) {
	return typeof e == "symbol" ? 1 : e === null ? 2 : e === void 0 ? 3 : e === e ? 0 : 4;
}
var Pr = (e, t, n) => {
	if (e !== t) {
		let r = Nr(e), i = Nr(t);
		if (r === i && r === 0) {
			if (e < t) return n === "desc" ? 1 : -1;
			if (e > t) return n === "desc" ? -1 : 1;
		}
		return n === "desc" ? i - r : r - i;
	}
	return 0;
};
//#endregion
//#region node_modules/es-toolkit/dist/compat/predicate/isSymbol.mjs
function Fr(e) {
	return typeof e == "symbol" || e instanceof Symbol;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/_internal/isKey.mjs
var Ir = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, Lr = /^\w*$/;
function Rr(e, t) {
	return Array.isArray(e) ? !1 : typeof e == "number" || typeof e == "boolean" || e == null || Fr(e) ? !0 : typeof e == "string" && (Lr.test(e) || !Ir.test(e)) || t != null && Object.hasOwn(t, e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/orderBy.mjs
function zr(e, t, n, r) {
	if (e == null) return [];
	n = r ? void 0 : n, Array.isArray(e) || (e = Object.values(e)), Array.isArray(t) || (t = t == null ? [null] : [t]), t.length === 0 && (t = [null]), Array.isArray(n) || (n = n == null ? [] : [n]), n = n.map((e) => String(e));
	let i = (e, t) => {
		let n = e;
		for (let e = 0; e < t.length && n != null; ++e) n = n[t[e]];
		return n;
	}, a = (e, t) => t == null || e == null ? t : typeof e == "object" && "key" in e ? Object.hasOwn(t, e.key) ? t[e.key] : i(t, e.path) : typeof e == "function" ? e(t) : Array.isArray(e) ? i(t, e) : typeof t == "object" ? t[e] : t, o = t.map((e) => (Array.isArray(e) && e.length === 1 && (e = e[0]), e == null || typeof e == "function" || Array.isArray(e) || Rr(e) ? e : {
		key: e,
		path: xt(e)
	}));
	return e.map((e) => ({
		original: e,
		criteria: o.map((t) => a(t, e))
	})).slice().sort((e, t) => {
		for (let r = 0; r < o.length; r++) {
			let i = Pr(e.criteria[r], t.criteria[r], n[r]);
			if (i !== 0) return i;
		}
		return 0;
	}).map((e) => e.original);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/array/sortBy.mjs
function Br(e, ...t) {
	let n = t.length;
	return n > 1 && Mr(e, t[0], t[1]) ? t = [] : n > 2 && Mr(t[0], t[1], t[2]) && (t = [t[0]]), zr(e, jr(t), ["asc"]);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/legendSelectors.js
var Vr = (e) => e.legend.settings, Hr = (e) => e.legend.size;
B([(e) => e.legend.payload, Vr], (e, t) => {
	var n = t.itemSorter, r = e.flat(1);
	return n ? Br(r, n) : r;
});
//#endregion
//#region node_modules/recharts/es6/util/useElementOffset.js
function Ur(e, t) {
	return Jr(e) || qr(e, t) || Gr(e, t) || Wr();
}
function Wr() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Gr(e, t) {
	if (e) {
		if (typeof e == "string") return Kr(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Kr(e, t) : void 0;
	}
}
function Kr(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function qr(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Jr(e) {
	if (Array.isArray(e)) return e;
}
var Yr = 1;
function Xr(e, t) {
	return Math.abs(e.height - t.height) > Yr || Math.abs(e.left - t.left) > Yr || Math.abs(e.top - t.top) > Yr || Math.abs(e.width - t.width) > Yr;
}
function Zr(e) {
	var t = e.getBoundingClientRect();
	return {
		height: t.height,
		left: t.left,
		top: t.top,
		width: t.width
	};
}
function Qr() {
	var e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : [], t = Ur((0, C.useState)({
		height: 0,
		left: 0,
		top: 0,
		width: 0
	}), 2), n = t[0], r = t[1], i = (0, C.useRef)(null), a = (0, C.useRef)(n);
	a.current = n;
	var o = (0, C.useCallback)((e) => {
		if (i.current != null && (i.current.disconnect(), i.current = null), e != null) {
			var t = Zr(e);
			if (Xr(t, a.current) && r(t), typeof ResizeObserver < "u") {
				var n = new ResizeObserver(() => {
					var t = Zr(e);
					Xr(t, a.current) && r(t);
				});
				n.observe(e), i.current = n;
			}
		}
	}, [...e]);
	return (0, C.useEffect)(() => () => {
		var e;
		(e = i.current) == null || e.disconnect();
	}, []), [n, o];
}
//#endregion
//#region node_modules/redux/dist/redux.mjs
function $r(e) {
	return `Minified Redux error #${e}; visit https://redux.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
var ei = typeof Symbol == "function" && Symbol.observable || "@@observable", ti = () => Math.random().toString(36).substring(7).split("").join("."), ni = {
	INIT: `@@redux/INIT${/* @__PURE__ */ ti()}`,
	REPLACE: `@@redux/REPLACE${/* @__PURE__ */ ti()}`,
	PROBE_UNKNOWN_ACTION: () => `@@redux/PROBE_UNKNOWN_ACTION${ti()}`
};
function ri(e) {
	if (typeof e != "object" || !e) return !1;
	let t = e;
	for (; Object.getPrototypeOf(t) !== null;) t = Object.getPrototypeOf(t);
	return Object.getPrototypeOf(e) === t || Object.getPrototypeOf(e) === null;
}
function ii(e, t, n) {
	if (typeof e != "function") throw Error($r(2));
	if (typeof t == "function" && typeof n == "function" || typeof n == "function" && typeof arguments[3] == "function") throw Error($r(0));
	if (typeof t == "function" && n === void 0 && (n = t, t = void 0), n !== void 0) {
		if (typeof n != "function") throw Error($r(1));
		return n(ii)(e, t);
	}
	let r = e, i = t, a = /* @__PURE__ */ new Map(), o = a, s = 0, c = !1;
	function l() {
		o === a && (o = /* @__PURE__ */ new Map(), a.forEach((e, t) => {
			o.set(t, e);
		}));
	}
	function u() {
		if (c) throw Error($r(3));
		return i;
	}
	function d(e) {
		if (typeof e != "function") throw Error($r(4));
		if (c) throw Error($r(5));
		let t = !0;
		l();
		let n = s++;
		return o.set(n, e), function() {
			if (t) {
				if (c) throw Error($r(6));
				t = !1, l(), o.delete(n), a = null;
			}
		};
	}
	function f(e) {
		if (!ri(e)) throw Error($r(7));
		if (e.type === void 0) throw Error($r(8));
		if (typeof e.type != "string") throw Error($r(17));
		if (c) throw Error($r(9));
		try {
			c = !0, i = r(i, e);
		} finally {
			c = !1;
		}
		return (a = o).forEach((e) => {
			e();
		}), e;
	}
	function p(e) {
		if (typeof e != "function") throw Error($r(10));
		r = e, f({ type: ni.REPLACE });
	}
	function m() {
		let e = d;
		return {
			subscribe(t) {
				if (typeof t != "object" || !t) throw Error($r(11));
				function n() {
					let e = t;
					e.next && e.next(u());
				}
				return n(), { unsubscribe: e(n) };
			},
			[ei]() {
				return this;
			}
		};
	}
	return f({ type: ni.INIT }), {
		dispatch: f,
		subscribe: d,
		getState: u,
		replaceReducer: p,
		[ei]: m
	};
}
function ai(e) {
	Object.keys(e).forEach((t) => {
		let n = e[t];
		if (n(void 0, { type: ni.INIT }) === void 0) throw Error($r(12));
		if (n(void 0, { type: ni.PROBE_UNKNOWN_ACTION() }) === void 0) throw Error($r(13));
	});
}
function oi(e) {
	let t = Object.keys(e), n = {};
	for (let r = 0; r < t.length; r++) {
		let i = t[r];
		typeof e[i] == "function" && (n[i] = e[i]);
	}
	let r = Object.keys(n), i;
	try {
		ai(n);
	} catch (e) {
		i = e;
	}
	return function(e = {}, t) {
		if (i) throw i;
		let a = !1, o = {};
		for (let i = 0; i < r.length; i++) {
			let s = r[i], c = n[s], l = e[s], u = c(l, t);
			if (u === void 0) throw t && t.type, Error($r(14));
			o[s] = u, a = a || u !== l;
		}
		return a = a || r.length !== Object.keys(e).length, a ? o : e;
	};
}
function si(...e) {
	return e.length === 0 ? (e) => e : e.length === 1 ? e[0] : e.reduce((e, t) => (...n) => e(t(...n)));
}
function ci(...e) {
	return (t) => (n, r) => {
		let i = t(n, r), a = () => {
			throw Error($r(15));
		}, o = {
			getState: i.getState,
			dispatch: (e, ...t) => a(e, ...t)
		};
		return a = si(...e.map((e) => e(o)))(i.dispatch), {
			...i,
			dispatch: a
		};
	};
}
function li(e) {
	return ri(e) && "type" in e && typeof e.type == "string";
}
//#endregion
//#region node_modules/immer/dist/immer.mjs
var ui = Symbol.for("immer-nothing"), di = Symbol.for("immer-draftable"), fi = Symbol.for("immer-state");
function pi(e, ...t) {
	throw Error(`[Immer] minified error nr: ${e}. Full error at: https://bit.ly/3cXEKWf`);
}
var mi = Object, hi = mi.getPrototypeOf, gi = "constructor", _i = "prototype", vi = "configurable", yi = "enumerable", bi = "writable", xi = "value", Si = (e) => !!e && !!e[fi];
function Ci(e) {
	var t;
	return e ? Ei(e) || Ni(e) || !!e[di] || !!((t = e[gi]) != null && t[di]) || Pi(e) || Fi(e) : !1;
}
var wi = mi[_i][gi].toString(), Ti = /* @__PURE__ */ new WeakMap();
function Ei(e) {
	if (!e || !Ii(e)) return !1;
	let t = hi(e);
	if (t === null || t === mi[_i]) return !0;
	let n = mi.hasOwnProperty.call(t, gi) && t[gi];
	if (n === Object) return !0;
	if (!Li(n)) return !1;
	let r = Ti.get(n);
	return r === void 0 && (r = Function.toString.call(n), Ti.set(n, r)), r === wi;
}
function Di(e, t, n = !0) {
	Oi(e) === 0 ? (n ? Reflect.ownKeys(e) : mi.keys(e)).forEach((n) => {
		t(n, e[n], e);
	}) : e.forEach((n, r) => t(r, n, e));
}
function Oi(e) {
	let t = e[fi];
	return t ? t.type_ : Ni(e) ? 1 : Pi(e) ? 2 : Fi(e) ? 3 : 0;
}
var ki = (e, t, n = Oi(e)) => n === 2 ? e.has(t) : mi[_i].hasOwnProperty.call(e, t), Ai = (e, t, n = Oi(e)) => n === 2 ? e.get(t) : e[t], ji = (e, t, n, r = Oi(e)) => {
	r === 2 ? e.set(t, n) : r === 3 ? e.add(n) : e[t] = n;
};
function Mi(e, t) {
	return e === t ? e !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
var Ni = Array.isArray, Pi = (e) => e instanceof Map, Fi = (e) => e instanceof Set, Ii = (e) => typeof e == "object", Li = (e) => typeof e == "function", Ri = (e) => typeof e == "boolean";
function zi(e) {
	let t = +e;
	return Number.isInteger(t) && String(t) === e;
}
var Bi = (e) => e.copy_ || e.base_, Vi = (e) => e.modified_ ? e.copy_ : e.base_;
function Hi(e, t) {
	if (Pi(e)) return new Map(e);
	if (Fi(e)) return new Set(e);
	if (Ni(e)) return Array[_i].slice.call(e);
	let n = Ei(e);
	if (t === !0 || t === "class_only" && !n) {
		let t = mi.getOwnPropertyDescriptors(e);
		delete t[fi];
		let n = Reflect.ownKeys(t);
		for (let r = 0; r < n.length; r++) {
			let i = n[r], a = t[i];
			a[bi] === !1 && (a[bi] = !0, a[vi] = !0), (a.get || a.set) && (t[i] = {
				[vi]: !0,
				[bi]: !0,
				[yi]: a[yi],
				[xi]: e[i]
			});
		}
		return mi.create(hi(e), t);
	} else {
		let t = hi(e);
		if (t !== null && n) return { ...e };
		let r = mi.create(t);
		return mi.assign(r, e);
	}
}
function Ui(e, t = !1) {
	return Ki(e) || Si(e) || !Ci(e) ? e : (Oi(e) > 1 && mi.defineProperties(e, {
		set: Gi,
		add: Gi,
		clear: Gi,
		delete: Gi
	}), mi.freeze(e), t && Di(e, (e, t) => {
		Ui(t, !0);
	}, !1), e);
}
function Wi() {
	pi(2);
}
var Gi = { [xi]: Wi };
function Ki(e) {
	return e === null || !Ii(e) || mi.isFrozen(e);
}
var qi = "MapSet", V = "Patches", H = "ArrayMethods", Ji = {};
function Yi(e) {
	let t = Ji[e];
	return t || pi(0, e), t;
}
var Xi = (e) => !!Ji[e], Zi, Qi = () => Zi, $i = (e, t) => ({
	drafts_: [],
	parent_: e,
	immer_: t,
	canAutoFreeze_: !0,
	unfinalizedDrafts_: 0,
	handledSet_: /* @__PURE__ */ new Set(),
	processedForPatches_: /* @__PURE__ */ new Set(),
	mapSetPlugin_: Xi(qi) ? Yi(qi) : void 0,
	arrayMethodsPlugin_: Xi(H) ? Yi(H) : void 0
});
function ea(e, t) {
	t && (e.patchPlugin_ = Yi(V), e.patches_ = [], e.inversePatches_ = [], e.patchListener_ = t);
}
function ta(e) {
	na(e), e.drafts_.forEach(ia), e.drafts_ = null;
}
function na(e) {
	e === Zi && (Zi = e.parent_);
}
var ra = (e) => Zi = $i(Zi, e);
function ia(e) {
	let t = e[fi];
	t.type_ === 0 || t.type_ === 1 ? t.revoke_() : t.revoked_ = !0;
}
function aa(e, t) {
	t.unfinalizedDrafts_ = t.drafts_.length;
	let n = t.drafts_[0];
	if (e !== void 0 && e !== n) {
		n[fi].modified_ && (ta(t), pi(4)), Ci(e) && (e = oa(t, e));
		let { patchPlugin_: r } = t;
		r && r.generateReplacementPatches_(n[fi].base_, e, t);
	} else e = oa(t, n);
	return sa(t, e, !0), ta(t), t.patches_ && t.patchListener_(t.patches_, t.inversePatches_), e === ui ? void 0 : e;
}
function oa(e, t) {
	if (Ki(t)) return t;
	let n = t[fi];
	if (!n) return ha(t, e.handledSet_, e);
	if (!la(n, e)) return t;
	if (!n.modified_) return n.base_;
	if (!n.finalized_) {
		let { callbacks_: t } = n;
		if (t) for (; t.length > 0;) t.pop()(e);
		pa(n, e);
	}
	return n.copy_;
}
function sa(e, t, n = !1) {
	!e.parent_ && e.immer_.autoFreeze_ && e.canAutoFreeze_ && Ui(t, n);
}
function ca(e) {
	e.finalized_ = !0, e.scope_.unfinalizedDrafts_--;
}
var la = (e, t) => e.scope_ === t, ua = [];
function da(e, t, n, r) {
	var i;
	let a = Bi(e), o = e.type_;
	if (r !== void 0 && Ai(a, r, o) === t) {
		ji(a, r, n, o);
		return;
	}
	if (!e.draftLocations_) {
		let t = e.draftLocations_ = /* @__PURE__ */ new Map();
		Di(a, (e, n) => {
			if (Si(n)) {
				let r = t.get(n) || [];
				r.push(e), t.set(n, r);
			}
		});
	}
	let s = (i = e.draftLocations_.get(t)) == null ? ua : i;
	for (let e of s) ji(a, e, n, o);
}
function fa(e, t, n) {
	e.callbacks_.push(function(r) {
		var i, a;
		let o = t;
		if (!o || !la(o, r)) return;
		(i = r.mapSetPlugin_) == null || i.fixSetContents(o);
		let s = Vi(o);
		da(e, (a = o.draft_) == null ? o : a, s, n), pa(o, r);
	});
}
function pa(e, t) {
	var n, r;
	if (e.modified_ && !e.finalized_ && (e.type_ === 3 || e.type_ === 1 && e.allIndicesReassigned_ || ((n = (r = e.assigned_) == null ? void 0 : r.size) == null ? 0 : n) > 0)) {
		let { patchPlugin_: n } = t;
		if (n) {
			let r = n.getPath(e);
			r && n.generatePatches_(e, r, t);
		}
		ca(e);
	}
}
function ma(e, t, n) {
	let { scope_: r } = e;
	if (Si(n)) {
		let i = n[fi];
		la(i, r) && i.callbacks_.push(function() {
			wa(e), da(e, n, Vi(i), t);
		});
	} else Ci(n) && e.callbacks_.push(function() {
		let i = Bi(e);
		if (e.type_ === 3) i.has(n) && ha(n, r.handledSet_, r);
		else if (Ai(i, t, e.type_) === n) {
			var a;
			r.drafts_.length > 1 && ((a = e.assigned_.get(t)) != null && a) === !0 && e.copy_ && ha(Ai(e.copy_, t, e.type_), r.handledSet_, r);
		}
	});
}
function ha(e, t, n) {
	return !n.immer_.autoFreeze_ && n.unfinalizedDrafts_ < 1 || Si(e) || t.has(e) || !Ci(e) || Ki(e) ? e : (t.add(e), Di(e, (r, i) => {
		if (Si(i)) {
			let t = i[fi];
			la(t, n) && (ji(e, r, Vi(t), e.type_), ca(t));
		} else Ci(i) && ha(i, t, n);
	}), e);
}
function ga(e, t) {
	let n = Ni(e), r = {
		type_: +!!n,
		scope_: t ? t.scope_ : Qi(),
		modified_: !1,
		finalized_: !1,
		assigned_: void 0,
		parent_: t,
		base_: e,
		draft_: null,
		copy_: null,
		revoke_: null,
		isManual_: !1,
		callbacks_: void 0
	}, i = r, a = _a;
	n && (i = [r], a = va);
	let { revoke: o, proxy: s } = Proxy.revocable(i, a);
	return r.draft_ = s, r.revoke_ = o, [s, r];
}
var _a = {
	get(e, t) {
		if (t === fi) return e;
		let n = e.scope_.arrayMethodsPlugin_, r = e.type_ === 1 && typeof t == "string";
		if (r && n != null && n.isArrayOperationMethod(t)) return n.createMethodInterceptor(e, t);
		let i = Bi(e);
		if (!ki(i, t, e.type_)) return xa(e, i, t);
		let a = i[t];
		if (e.finalized_ || !Ci(a) || r && e.operationMethod && n != null && n.isMutatingArrayMethod(e.operationMethod) && zi(t)) return a;
		if (a === ya(e.base_, t) || ba(e, t, a)) {
			wa(e);
			let n = e.type_ === 1 ? +t : t, r = U(e.scope_, a, e, n);
			return e.copy_[n] = r;
		}
		return a;
	},
	has(e, t) {
		return t in Bi(e);
	},
	ownKeys(e) {
		return Reflect.ownKeys(Bi(e));
	},
	set(e, t, n) {
		let r = Sa(Bi(e), t);
		if (r != null && r.set) return r.set.call(e.draft_, n), !0;
		if (!e.modified_) {
			let r = ya(Bi(e), t), i = r == null ? void 0 : r[fi];
			if (i && i.base_ === n) return e.copy_[t] = n, e.assigned_.set(t, !1), !0;
			if (Mi(n, r) && (n !== void 0 || ki(e.base_, t, e.type_))) return !0;
			wa(e), Ca(e);
		}
		return e.copy_[t] === n && (n !== void 0 || ki(e.copy_, t, e.type_)) || Number.isNaN(n) && Number.isNaN(e.copy_[t]) ? !0 : (e.copy_[t] = n, e.assigned_.set(t, !0), ma(e, t, n), !0);
	},
	deleteProperty(e, t) {
		return wa(e), ya(e.base_, t) !== void 0 || t in e.base_ ? (e.assigned_.set(t, !1), Ca(e)) : e.assigned_.delete(t), e.copy_ && delete e.copy_[t], !0;
	},
	getOwnPropertyDescriptor(e, t) {
		let n = Bi(e), r = Reflect.getOwnPropertyDescriptor(n, t);
		return r && {
			[bi]: !0,
			[vi]: e.type_ !== 1 || t !== "length",
			[yi]: r[yi],
			[xi]: n[t]
		};
	},
	defineProperty() {
		pi(11);
	},
	getPrototypeOf(e) {
		return hi(e.base_);
	},
	setPrototypeOf() {
		pi(12);
	}
}, va = {};
for (let e in _a) {
	let t = _a[e];
	va[e] = function() {
		let e = arguments;
		return e[0] = e[0][0], t.apply(this, e);
	};
}
va.deleteProperty = function(e, t) {
	return va.set.call(this, e, t, void 0);
}, va.set = function(e, t, n) {
	return _a.set.call(this, e[0], t, n, e[0]);
};
function ya(e, t) {
	let n = e[fi];
	return (n ? Bi(n) : e)[t];
}
function ba(e, t, n) {
	var r;
	return e.type_ !== 1 || !e.allIndicesReassigned_ || (r = e.assigned_) != null && r.get(t) || !Ci(n) || n[fi] ? !1 : e.baseRefs_.has(n);
}
function xa(e, t, n) {
	var r;
	let i = Sa(t, n);
	return i ? xi in i ? i[xi] : (r = i.get) == null ? void 0 : r.call(e.draft_) : void 0;
}
function Sa(e, t) {
	if (!(t in e)) return;
	let n = hi(e);
	for (; n;) {
		let e = Object.getOwnPropertyDescriptor(n, t);
		if (e) return e;
		n = hi(n);
	}
}
function Ca(e) {
	e.modified_ || (e.modified_ = !0, e.parent_ && Ca(e.parent_));
}
function wa(e) {
	e.copy_ || (e.assigned_ = /* @__PURE__ */ new Map(), e.copy_ = Hi(e.base_, e.scope_.immer_.useStrictShallowCopy_));
}
var Ta = class {
	constructor(e) {
		this.autoFreeze_ = !0, this.useStrictShallowCopy_ = !1, this.useStrictIteration_ = !1, this.produce = (e, t, n) => {
			if (Li(e) && !Li(t)) {
				let n = t;
				t = e;
				let r = this;
				return function(e = n, ...i) {
					return r.produce(e, (e) => t.call(this, e, ...i));
				};
			}
			Li(t) || pi(6), n !== void 0 && !Li(n) && pi(7);
			let r;
			if (Ci(e)) {
				let i = ra(this), a = U(i, e, void 0), o = !0;
				try {
					r = t(a), o = !1;
				} finally {
					o ? ta(i) : na(i);
				}
				return ea(i, n), aa(r, i);
			} else if (!e || !Ii(e)) {
				if (r = t(e), r === void 0 && (r = e), r === ui && (r = void 0), this.autoFreeze_ && Ui(r, !0), n) {
					let t = [], i = [];
					Yi(V).generateReplacementPatches_(e, r, {
						patches_: t,
						inversePatches_: i
					}), n(t, i);
				}
				return r;
			} else pi(1, e);
		}, this.produceWithPatches = (e, t) => {
			if (Li(e)) return (t, ...n) => this.produceWithPatches(t, (t) => e(t, ...n));
			let n, r;
			return [
				this.produce(e, t, (e, t) => {
					n = e, r = t;
				}),
				n,
				r
			];
		}, Ri(e == null ? void 0 : e.autoFreeze) && this.setAutoFreeze(e.autoFreeze), Ri(e == null ? void 0 : e.useStrictShallowCopy) && this.setUseStrictShallowCopy(e.useStrictShallowCopy), Ri(e == null ? void 0 : e.useStrictIteration) && this.setUseStrictIteration(e.useStrictIteration);
	}
	createDraft(e) {
		Ci(e) || pi(8), Si(e) && (e = Ea(e));
		let t = ra(this), n = U(t, e, void 0);
		return n[fi].isManual_ = !0, na(t), n;
	}
	finishDraft(e, t) {
		let n = e && e[fi];
		(!n || !n.isManual_) && pi(9);
		let { scope_: r } = n;
		return ea(r, t), aa(void 0, r);
	}
	setAutoFreeze(e) {
		this.autoFreeze_ = e;
	}
	setUseStrictShallowCopy(e) {
		this.useStrictShallowCopy_ = e;
	}
	setUseStrictIteration(e) {
		this.useStrictIteration_ = e;
	}
	shouldUseStrictIteration() {
		return this.useStrictIteration_;
	}
	applyPatches(e, t) {
		let n;
		for (n = t.length - 1; n >= 0; n--) {
			let r = t[n];
			if (r.path.length === 0 && r.op === "replace") {
				e = r.value;
				break;
			}
		}
		n > -1 && (t = t.slice(n + 1));
		let r = Yi(V).applyPatches_;
		return Si(e) ? r(e, t) : this.produce(e, (e) => r(e, t));
	}
};
function U(e, t, n, r) {
	var i, a;
	let [o, s] = Pi(t) ? Yi(qi).proxyMap_(t, n) : Fi(t) ? Yi(qi).proxySet_(t, n) : ga(t, n);
	return ((i = n == null ? void 0 : n.scope_) == null ? Qi() : i).drafts_.push(o), s.callbacks_ = (a = n == null ? void 0 : n.callbacks_) == null ? [] : a, s.key_ = r, n && r !== void 0 ? fa(n, s, r) : s.callbacks_.push(function(e) {
		var t;
		(t = e.mapSetPlugin_) == null || t.fixSetContents(s);
		let { patchPlugin_: n } = e;
		s.modified_ && n && n.generatePatches_(s, [], e);
	}), o;
}
function Ea(e) {
	return Si(e) || pi(10, e), Da(e);
}
function Da(e) {
	if (!Ci(e) || Ki(e)) return e;
	let t = e[fi], n, r = !0;
	if (t) {
		if (!t.modified_) return t.base_;
		t.finalized_ = !0, n = Hi(e, t.scope_.immer_.useStrictShallowCopy_), r = t.scope_.immer_.shouldUseStrictIteration();
	} else n = Hi(e, !0);
	return Di(n, (e, t) => {
		ji(n, e, Da(t));
	}, r), t && (t.finalized_ = !1), n;
}
var Oa = new Ta().produce, W = (e) => e;
//#endregion
//#region node_modules/redux-thunk/dist/redux-thunk.mjs
function ka(e) {
	return ({ dispatch: t, getState: n }) => (r) => (i) => typeof i == "function" ? i(t, n, e) : r(i);
}
var Aa = ka(), ja = ka, Ma = typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ ? window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__ : function() {
	if (arguments.length !== 0) return typeof arguments[0] == "object" ? si : si.apply(null, arguments);
};
typeof window < "u" && window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__;
function Na(e, t) {
	function n(...n) {
		if (t) {
			let r = t(...n);
			if (!r) throw Error(Vo(0));
			return {
				type: e,
				payload: r.payload,
				..."meta" in r && { meta: r.meta },
				..."error" in r && { error: r.error }
			};
		}
		return {
			type: e,
			payload: n[0]
		};
	}
	return n.toString = () => `${e}`, n.type = e, n.match = (t) => li(t) && t.type === e, n;
}
var Pa = class e extends Array {
	constructor(...t) {
		super(...t), Object.setPrototypeOf(this, e.prototype);
	}
	static get [Symbol.species]() {
		return e;
	}
	concat(...e) {
		return super.concat.apply(this, e);
	}
	prepend(...t) {
		return t.length === 1 && Array.isArray(t[0]) ? new e(...t[0].concat(this)) : new e(...t.concat(this));
	}
};
function Fa(e) {
	return Ci(e) ? Oa(e, () => {}) : e;
}
function Ia(e, t, n) {
	return e.has(t) ? e.get(t) : e.set(t, n(t)).get(t);
}
function La(e) {
	return typeof e == "boolean";
}
var Ra = () => function(e) {
	let { thunk: t = !0, immutableCheck: n = !0, serializableCheck: r = !0, actionCreatorCheck: i = !0 } = e == null ? {} : e, a = new Pa();
	return t && (La(t) ? a.push(Aa) : a.push(ja(t.extraArgument))), a;
}, za = "RTK_autoBatch", G = () => (e) => ({
	payload: e,
	meta: { [za]: !0 }
}), Ba = (e) => (t) => {
	setTimeout(t, e);
}, Va = (e, t) => (n) => {
	let r = !1, i = () => {
		r || (r = !0, cancelAnimationFrame(a), clearTimeout(o), n());
	}, a = e(i), o = setTimeout(i, t);
}, Ha = (e = { type: "raf" }) => (t) => (...n) => {
	let r = t(...n), i = !0, a = !1, o = !1, s = /* @__PURE__ */ new Set(), c = e.type === "tick" ? queueMicrotask : e.type === "raf" ? typeof window < "u" && window.requestAnimationFrame ? Va(window.requestAnimationFrame, 100) : Ba(10) : e.type === "callback" ? e.queueNotification : Ba(e.timeout), l = () => {
		o = !1, a && (a = !1, s.forEach((e) => e()));
	};
	return Object.assign({}, r, {
		subscribe(e) {
			let t = r.subscribe(() => i && e());
			return s.add(e), () => {
				t(), s.delete(e);
			};
		},
		dispatch(e) {
			try {
				var t;
				return i = !(!(e == null || (t = e.meta) == null) && t[za]), a = !i, a && (o || (o = !0, c(l))), r.dispatch(e);
			} finally {
				i = !0;
			}
		}
	});
}, Ua = (e) => function(t) {
	let { autoBatch: n = !0 } = t == null ? {} : t, r = new Pa(e);
	return n && r.push(Ha(typeof n == "object" ? n : void 0)), r;
};
function Wa(e) {
	let t = Ra(), { reducer: n = void 0, middleware: r, devTools: i = !0, duplicateMiddlewareCheck: a = !0, preloadedState: o = void 0, enhancers: s = void 0 } = e || {}, c;
	if (typeof n == "function") c = n;
	else if (ri(n)) c = oi(n);
	else throw Error(Vo(1));
	let l;
	l = typeof r == "function" ? r(t) : t();
	let u = si;
	i && (u = Ma({
		trace: !1,
		...typeof i == "object" && i
	}));
	let d = Ua(ci(...l)), f = typeof s == "function" ? s(d) : d(), p = u(...f);
	return ii(c, o, p);
}
function Ga(e) {
	let t = {}, n = [], r, i = {
		addCase(e, n) {
			let r = typeof e == "string" ? e : e.type;
			if (!r) throw Error(Vo(28));
			if (r in t) throw Error(Vo(29));
			return t[r] = n, i;
		},
		addAsyncThunk(e, r) {
			return r.pending && (t[e.pending.type] = r.pending), r.rejected && (t[e.rejected.type] = r.rejected), r.fulfilled && (t[e.fulfilled.type] = r.fulfilled), r.settled && n.push({
				matcher: e.settled,
				reducer: r.settled
			}), i;
		},
		addMatcher(e, t) {
			return n.push({
				matcher: e,
				reducer: t
			}), i;
		},
		addDefaultCase(e) {
			return r = e, i;
		}
	};
	return e(i), [
		t,
		n,
		r
	];
}
function Ka(e) {
	return typeof e == "function";
}
function qa(e, t) {
	let [n, r, i] = Ga(t), a;
	if (Ka(e)) a = () => Fa(e());
	else {
		let t = Fa(e);
		a = () => t;
	}
	function o(e = a(), t) {
		let o = [n[t.type], ...r.filter(({ matcher: e }) => e(t)).map(({ reducer: e }) => e)];
		return o.filter((e) => !!e).length === 0 && (o = [i]), o.reduce((e, n) => {
			if (n) if (Si(e)) {
				let r = n(e, t);
				return r === void 0 ? e : r;
			} else if (Ci(e)) return Oa(e, (e) => n(e, t));
			else {
				let r = n(e, t);
				if (r === void 0) {
					if (e === null) return e;
					throw Error("A case reducer on a non-draftable value must not return undefined");
				}
				return r;
			}
			return e;
		}, e);
	}
	return o.getInitialState = a, o;
}
var Ja = "ModuleSymbhasOwnPr-0123456789ABCDEFGHNRVfgctiUvz_KqYTJkLxpZXIjQW", Ya = (e = 21) => {
	let t = "", n = e;
	for (; n--;) t += Ja[Math.random() * 64 | 0];
	return t;
}, Xa = /* @__PURE__ */ Symbol.for("rtk-slice-createasyncthunk");
function Za(e, t) {
	return `${e}/${t}`;
}
function Qa({ creators: e } = {}) {
	var t;
	let n = e == null || (t = e.asyncThunk) == null ? void 0 : t[Xa];
	return function(e) {
		let { name: t, reducerPath: r = t } = e;
		if (!t) throw Error(Vo(11));
		let i = (typeof e.reducers == "function" ? e.reducers(to()) : e.reducers) || {}, a = Object.keys(i), o = {
			sliceCaseReducersByName: {},
			sliceCaseReducersByType: {},
			actionCreators: {},
			sliceMatchers: []
		}, s = {
			addCase(e, t) {
				let n = typeof e == "string" ? e : e.type;
				if (!n) throw Error(Vo(12));
				if (n in o.sliceCaseReducersByType) throw Error(Vo(13));
				return o.sliceCaseReducersByType[n] = t, s;
			},
			addMatcher(e, t) {
				return o.sliceMatchers.push({
					matcher: e,
					reducer: t
				}), s;
			},
			exposeAction(e, t) {
				return o.actionCreators[e] = t, s;
			},
			exposeCaseReducer(e, t) {
				return o.sliceCaseReducersByName[e] = t, s;
			}
		};
		a.forEach((r) => {
			let a = i[r], o = {
				reducerName: r,
				type: Za(t, r),
				createNotation: typeof e.reducers == "function"
			};
			ro(a) ? ao(o, a, s, n) : no(o, a, s);
		});
		function c() {
			let [t = {}, n = [], r = void 0] = typeof e.extraReducers == "function" ? Ga(e.extraReducers) : [e.extraReducers], i = {
				...t,
				...o.sliceCaseReducersByType
			};
			return qa(e.initialState, (e) => {
				for (let t in i) e.addCase(t, i[t]);
				for (let t of o.sliceMatchers) e.addMatcher(t.matcher, t.reducer);
				for (let t of n) e.addMatcher(t.matcher, t.reducer);
				r && e.addDefaultCase(r);
			});
		}
		let l = (e) => e, u = /* @__PURE__ */ new Map(), d = /* @__PURE__ */ new WeakMap(), f;
		function p(e, t) {
			return f || (f = c()), f(e, t);
		}
		function m() {
			return f || (f = c()), f.getInitialState();
		}
		function h(t, n = !1) {
			function r(e) {
				let i = e[t];
				return i === void 0 && n && (i = Ia(d, r, m)), i;
			}
			function i(t = l) {
				return Ia(Ia(u, n, () => /* @__PURE__ */ new WeakMap()), t, () => {
					var r;
					let i = {};
					for (let [a, o] of Object.entries((r = e.selectors) == null ? {} : r)) i[a] = $a(o, t, () => Ia(d, t, m), n);
					return i;
				});
			}
			return {
				reducerPath: t,
				getSelectors: i,
				get selectors() {
					return i(r);
				},
				selectSlice: r
			};
		}
		let g = {
			name: t,
			reducer: p,
			actions: o.actionCreators,
			caseReducers: o.sliceCaseReducersByName,
			getInitialState: m,
			...h(r),
			injectInto(e, { reducerPath: t, ...n } = {}) {
				let i = t == null ? r : t;
				return e.inject({
					reducerPath: i,
					reducer: p
				}, n), {
					...g,
					...h(i, !0)
				};
			}
		};
		return g;
	};
}
function $a(e, t, n, r) {
	function i(i, ...a) {
		let o = t(i);
		return o === void 0 && r && (o = n()), e(o, ...a);
	}
	return i.unwrapped = e, i;
}
var eo = /* @__PURE__ */ Qa();
function to() {
	function e(e, t) {
		return {
			_reducerDefinitionType: "asyncThunk",
			payloadCreator: e,
			...t
		};
	}
	return e.withTypes = () => e, {
		reducer(e) {
			return Object.assign({ [e.name](...t) {
				return e(...t);
			} }[e.name], { _reducerDefinitionType: "reducer" });
		},
		preparedReducer(e, t) {
			return {
				_reducerDefinitionType: "reducerWithPrepare",
				prepare: e,
				reducer: t
			};
		},
		asyncThunk: e
	};
}
function no({ type: e, reducerName: t, createNotation: n }, r, i) {
	let a, o;
	if ("reducer" in r) {
		if (n && !io(r)) throw Error(Vo(17));
		a = r.reducer, o = r.prepare;
	} else a = r;
	i.addCase(e, a).exposeCaseReducer(t, a).exposeAction(t, o ? Na(e, o) : Na(e));
}
function ro(e) {
	return e._reducerDefinitionType === "asyncThunk";
}
function io(e) {
	return e._reducerDefinitionType === "reducerWithPrepare";
}
function ao({ type: e, reducerName: t }, n, r, i) {
	if (!i) throw Error(Vo(18));
	let { payloadCreator: a, fulfilled: o, pending: s, rejected: c, settled: l, options: u } = n, d = i(e, a, u);
	r.exposeAction(t, d), o && r.addCase(d.fulfilled, o), s && r.addCase(d.pending, s), c && r.addCase(d.rejected, c), l && r.addMatcher(d.settled, l), r.exposeCaseReducer(t, {
		fulfilled: o || oo,
		pending: s || oo,
		rejected: c || oo,
		settled: l || oo
	});
}
function oo() {}
var so = "task", co = "listener", lo = "completed", uo = "cancelled", fo = `task-${uo}`, po = `task-${lo}`, mo = `${co}-${uo}`, ho = `${co}-${lo}`, go = class {
	constructor(e) {
		_r(this, "code", void 0), _r(this, "name", "TaskAbortError"), _r(this, "message", void 0), this.code = e, this.message = `${so} ${uo} (reason: ${e})`;
	}
}, _o = (e, t) => {
	if (typeof e != "function") throw TypeError(Vo(32));
}, vo = () => {}, yo = (e, t = vo) => (e.catch(t), e), bo = (e, t) => (e.addEventListener("abort", t, { once: !0 }), () => e.removeEventListener("abort", t)), xo = (e) => {
	if (e.aborted) throw new go(e.reason);
};
function So(e, t) {
	let n = vo;
	return new Promise((r, i) => {
		let a = () => i(new go(e.reason));
		if (e.aborted) {
			a();
			return;
		}
		n = bo(e, a), t.finally(() => n()).then(r, i);
	}).finally(() => {
		n = vo;
	});
}
var Co = async (e, t) => {
	try {
		return await Promise.resolve(), {
			status: "ok",
			value: await e()
		};
	} catch (e) {
		return {
			status: e instanceof go ? "cancelled" : "rejected",
			error: e
		};
	} finally {
		t == null || t();
	}
}, wo = (e) => (t) => yo(So(e, t).then((t) => (xo(e), t))), To = (e) => {
	let t = wo(e);
	return (e) => t(new Promise((t) => setTimeout(t, e)));
}, { assign: K } = Object, Eo = {}, Do = "listenerMiddleware", Oo = (e, t) => {
	let n = (t) => bo(e, () => t.abort(e.reason));
	return (r, i) => {
		_o(r, "taskExecutor");
		let a = new AbortController();
		n(a);
		let o = Co(async () => {
			xo(e), xo(a.signal);
			let t = await r({
				pause: wo(a.signal),
				delay: To(a.signal),
				signal: a.signal
			});
			return xo(a.signal), t;
		}, () => a.abort(po));
		return i != null && i.autoJoin && t.push(o.catch(vo)), {
			result: wo(e)(o),
			cancel() {
				a.abort(fo);
			}
		};
	};
}, ko = (e, t) => {
	let n = async (n, r) => {
		xo(t);
		let i = () => {}, a = [new Promise((t, r) => {
			let a = e({
				predicate: n,
				effect: (e, n) => {
					n.unsubscribe(), t([
						e,
						n.getState(),
						n.getOriginalState()
					]);
				}
			});
			i = () => {
				a(), r();
			};
		})];
		r != null && a.push(new Promise((e) => setTimeout(e, r, null)));
		try {
			let e = await So(t, Promise.race(a));
			return xo(t), e;
		} finally {
			i();
		}
	};
	return ((e, t) => yo(n(e, t)));
}, Ao = (e) => {
	let { type: t, actionCreator: n, matcher: r, predicate: i, effect: a } = e;
	if (t) i = Na(t).match;
	else if (n) t = n.type, i = n.match;
	else if (r) i = r;
	else if (!i) throw Error(Vo(21));
	return _o(a, "options.listener"), {
		predicate: i,
		type: t,
		effect: a
	};
}, jo = /* @__PURE__ */ K((e) => {
	let { type: t, predicate: n, effect: r } = Ao(e);
	return {
		id: Ya(),
		effect: r,
		type: t,
		predicate: n,
		pending: /* @__PURE__ */ new Set(),
		unsubscribe: () => {
			throw Error(Vo(22));
		}
	};
}, { withTypes: () => jo }), Mo = (e, t) => {
	let { type: n, effect: r, predicate: i } = Ao(t);
	return Array.from(e.values()).find((e) => (typeof n == "string" ? e.type === n : e.predicate === i) && e.effect === r);
}, No = (e) => {
	e.pending.forEach((e) => {
		e.abort(mo);
	});
}, Po = (e, t) => () => {
	for (let e of t.keys()) No(e);
	e.clear();
}, Fo = (e, t, n) => {
	try {
		e(t, n);
	} catch (e) {
		setTimeout(() => {
			throw e;
		}, 0);
	}
}, Io = /* @__PURE__ */ K(/* @__PURE__ */ Na(`${Do}/add`), { withTypes: () => Io }), Lo = /* @__PURE__ */ Na(`${Do}/removeAll`), Ro = /* @__PURE__ */ K(/* @__PURE__ */ Na(`${Do}/remove`), { withTypes: () => Ro }), zo = (...e) => {
	console.error(`${Do}/error`, ...e);
}, Bo = (e = {}) => {
	let t = /* @__PURE__ */ new Map(), n = /* @__PURE__ */ new Map(), r = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 0 : t;
		n.set(e, r + 1);
	}, i = (e) => {
		var t;
		let r = (t = n.get(e)) == null ? 1 : t;
		r === 1 ? n.delete(e) : n.set(e, r - 1);
	}, { extra: a, onError: o = zo } = e;
	_o(o, "onError");
	let s = (e) => (e.unsubscribe = () => t.delete(e.id), t.set(e.id, e), (t) => {
		e.unsubscribe(), t != null && t.cancelActive && No(e);
	}), c = ((e) => {
		var n;
		let r = (n = Mo(t, e)) == null ? jo(e) : n;
		return s(r);
	});
	K(c, { withTypes: () => c });
	let l = (e) => {
		let n = Mo(t, e);
		return n && (n.unsubscribe(), e.cancelActive && No(n)), !!n;
	};
	K(l, { withTypes: () => l });
	let u = async (e, n, s, l) => {
		let u = new AbortController(), d = ko(c, u.signal), f = [];
		try {
			e.pending.add(u), r(e), await Promise.resolve(e.effect(n, K({}, s, {
				getOriginalState: l,
				condition: (e, t) => d(e, t).then(Boolean),
				take: d,
				delay: To(u.signal),
				pause: wo(u.signal),
				extra: a,
				signal: u.signal,
				fork: Oo(u.signal, f),
				unsubscribe: e.unsubscribe,
				subscribe: () => {
					t.set(e.id, e);
				},
				cancelActiveListeners: () => {
					e.pending.forEach((e, t, n) => {
						e !== u && (e.abort(mo), n.delete(e));
					});
				},
				cancel: () => {
					u.abort(mo), e.pending.delete(u);
				},
				throwIfCancelled: () => {
					xo(u.signal);
				}
			})));
		} catch (e) {
			e instanceof go || Fo(o, e, { raisedBy: "effect" });
		} finally {
			await Promise.all(f), u.abort(ho), i(e), e.pending.delete(u);
		}
	}, d = Po(t, n);
	return {
		middleware: (e) => (n) => (r) => {
			if (!li(r)) return n(r);
			if (Io.match(r)) return c(r.payload);
			if (Lo.match(r)) {
				d();
				return;
			}
			if (Ro.match(r)) return l(r.payload);
			let i = e.getState(), a = () => {
				if (i === Eo) throw Error(Vo(23));
				return i;
			}, s;
			try {
				if (s = n(r), t.size > 0) {
					let n = e.getState(), s = Array.from(t.values());
					for (let t of s) {
						let s = !1;
						try {
							s = t.predicate(r, n, i);
						} catch (e) {
							s = !1, Fo(o, e, { raisedBy: "predicate" });
						}
						s && u(t, r, e, a);
					}
				}
			} finally {
				i = Eo;
			}
			return s;
		},
		startListening: c,
		stopListening: l,
		clearListeners: d
	};
};
function Vo(e) {
	return `Minified Redux Toolkit error #${e}; visit https://redux-toolkit.js.org/Errors?code=${e} for the full message or use the non-minified dev environment for full errors. `;
}
//#endregion
//#region node_modules/recharts/es6/state/layoutSlice.js
var Ho = eo({
	name: "chartLayout",
	initialState: {
		layoutType: "horizontal",
		width: 0,
		height: 0,
		margin: {
			top: 5,
			right: 5,
			bottom: 5,
			left: 5
		},
		scale: 1
	},
	reducers: {
		setLayout(e, t) {
			e.layoutType = t.payload;
		},
		setChartSize(e, t) {
			e.width = t.payload.width, e.height = t.payload.height;
		},
		setMargin(e, t) {
			var n, r, i, a;
			e.margin.top = (n = t.payload.top) == null ? 0 : n, e.margin.right = (r = t.payload.right) == null ? 0 : r, e.margin.bottom = (i = t.payload.bottom) == null ? 0 : i, e.margin.left = (a = t.payload.left) == null ? 0 : a;
		},
		setScale(e, t) {
			e.scale = t.payload;
		}
	}
}), Uo = Ho.actions, Wo = Uo.setMargin, Go = Uo.setLayout, Ko = Uo.setChartSize, qo = Uo.setScale, Jo = Ho.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getSliced.js
function Yo(e, t, n) {
	return Array.isArray(e) && e && t + n !== 0 ? e.slice(t, n + 1) : e;
}
//#endregion
//#region node_modules/recharts/es6/util/isWellBehavedNumber.js
function q(e) {
	return Number.isFinite(e);
}
function Xo(e) {
	return typeof e == "number" && e > 0 && Number.isFinite(e);
}
//#endregion
//#region node_modules/recharts/es6/util/ChartUtils.js
function Zo(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Qo(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Zo(Object(n), !0).forEach(function(t) {
			$o(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Zo(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function $o(e, t, n) {
	return (t = es(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function es(e) {
	var t = ts(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ts(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function ns(e, t, n) {
	return Lt(e) || Lt(t) ? n : At(t) ? St(e, t, n) : typeof t == "function" ? t(e) : n;
}
var rs = (e, t, n) => {
	if (t && n) {
		var r = n.width, i = n.height, a = t.align, o = t.verticalAlign, s = t.layout;
		if ((s === "vertical" || s === "horizontal" && o === "middle") && a !== "center" && I(e[a])) return Qo(Qo({}, e), {}, { [a]: e[a] + (r || 0) });
		if ((s === "horizontal" || s === "vertical" && a === "center") && o !== "middle" && I(e[o])) return Qo(Qo({}, e), {}, { [o]: e[o] + (i || 0) });
	}
	return e;
}, is = (e, t) => e === "horizontal" && t === "xAxis" || e === "vertical" && t === "yAxis" || e === "centric" && t === "angleAxis" || e === "radial" && t === "radiusAxis", as = (e, t) => {
	if (!t || t.length !== 2 || !I(t[0]) || !I(t[1])) return e;
	var n = Math.min(t[0], t[1]), r = Math.max(t[0], t[1]), i = [e[0], e[1]];
	return (!I(e[0]) || e[0] < n) && (i[0] = n), (!I(e[1]) || e[1] > r) && (i[1] = r), i[0] > r && (i[0] = r), i[1] < n && (i[1] = n), i;
}, os = {
	sign: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0, s = 0; s < n; ++s) {
				var c = e[s], l = c == null ? void 0 : c[i];
				if (l != null) {
					var u = l[1], d = l[0], f = Ot(u) ? d : u;
					f >= 0 ? (l[0] = a, a += f, l[1] = a) : (l[0] = o, o += f, l[1] = o);
				}
			}
		}
	},
	expand: mt,
	none: lt,
	silhouette: ht,
	wiggle: gt,
	positive: (e) => {
		var t, n = e.length;
		if (!(n <= 0)) {
			var r = (t = e[0]) == null ? void 0 : t.length;
			if (!(r == null || r <= 0)) for (var i = 0; i < r; ++i) for (var a = 0, o = 0; o < n; ++o) {
				var s = e[o], c = s == null ? void 0 : s[i];
				if (c != null) {
					var l = Ot(c[1]) ? c[0] : c[1];
					l >= 0 ? (c[0] = a, a += l, c[1] = a) : (c[0] = 0, c[1] = 0);
				}
			}
		}
	}
}, ss = (e, t, n) => {
	var r, i = (r = os[n]) == null ? lt : r, a = pt().keys(t).value((e, t) => Number(ns(e, t, 0))).order(ut).offset(i)(e);
	return a.forEach((n, r) => {
		n.forEach((n, i) => {
			var a = ns(e[i], t[r], 0);
			Array.isArray(a) && a.length === 2 && I(a[0]) && I(a[1]) && (n[0] = a[0], n[1] = a[1]);
		});
	}), a;
};
function cs(e) {
	return e == null ? void 0 : String(e);
}
var ls = (e) => {
	var t = e.axis, n = e.ticks, r = e.offset, i = e.bandSize, a = e.entry, o = e.index;
	if (t.type === "category") return n[o] ? n[o].coordinate + r : null;
	var s = ns(a, t.dataKey, t.scale.domain()[o]);
	if (Lt(s)) return null;
	var c = t.scale.map(s);
	return I(c) ? c - i / 2 + r : null;
}, us = (e) => {
	var t = e.numericAxis, n = t.scale.domain();
	if (t.type === "number") {
		var r = Math.min(n[0], n[1]), i = Math.max(n[0], n[1]);
		return r <= 0 && i >= 0 ? 0 : i < 0 ? i : r;
	}
	return n[0];
}, ds = (e) => {
	var t = e.flat(2).filter(I);
	return [Math.min(...t), Math.max(...t)];
}, fs = (e) => [e[0] === Infinity ? 0 : e[0], e[1] === -Infinity ? 0 : e[1]], ps = (e, t, n) => {
	if (!(e == null || Object.keys(e).length === 0)) return fs(Object.keys(e).reduce((r, i) => {
		var a = e[i];
		if (!a) return r;
		var o = a.stackedData.reduce((e, r) => {
			var i = ds(Yo(r, t, n));
			return !q(i[0]) || !q(i[1]) ? e : [Math.min(e[0], i[0]), Math.max(e[1], i[1])];
		}, [Infinity, -Infinity]);
		return [Math.min(o[0], r[0]), Math.max(o[1], r[1])];
	}, [Infinity, -Infinity]));
}, ms = /^dataMin[\s]*-[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, hs = /^dataMax[\s]*\+[\s]*([0-9]+([.]{1}[0-9]+){0,1})$/, gs = (e, t, n) => {
	if (e && e.scale && e.scale.bandwidth) {
		var r = e.scale.bandwidth();
		if (!n || r > 0) return r;
	}
	if (e && t && t.length >= 2) {
		for (var i = Br(t, (e) => e.coordinate), a = Infinity, o = 1, s = i.length; o < s; o++) {
			var c = i[o], l = i[o - 1];
			a = Math.min(((c == null ? void 0 : c.coordinate) || 0) - ((l == null ? void 0 : l.coordinate) || 0), a);
		}
		return a === Infinity ? 0 : a;
	}
	return n ? void 0 : 0;
};
function _s(e) {
	var t = e.tooltipEntrySettings, n = e.dataKey, r = e.payload, i = e.value, a = e.name;
	return Qo(Qo({}, t), {}, {
		dataKey: n,
		payload: r,
		value: i,
		name: a
	});
}
function vs(e, t) {
	if (e != null) return String(e);
	if (typeof t == "string") return t;
}
var ys = (e, t) => {
	if (t === "horizontal") return e.relativeX;
	if (t === "vertical") return e.relativeY;
}, bs = (e, t) => t === "centric" ? e.angle : e.radius, xs = (e) => e.layout.width, Ss = (e) => e.layout.height, Cs = (e) => e.layout.scale, ws = (e) => e.layout.margin, Ts = B((e) => e.cartesianAxis.xAxis, (e) => Object.values(e)), Es = B((e) => e.cartesianAxis.yAxis, (e) => Object.values(e)), Ds = "data-recharts-item-index";
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectChartOffsetInternal.js
function Os(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ks(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Os(Object(n), !0).forEach(function(t) {
			As(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Os(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function As(e, t, n) {
	return (t = js(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function js(e) {
	var t = Ms(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Ms(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Ns = (e) => e.brush.height;
function Ps(e) {
	return Es(e).reduce((e, t) => t.orientation === "left" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function Fs(e) {
	return Es(e).reduce((e, t) => t.orientation === "right" && !t.mirror && !t.hide ? e + (typeof t.width == "number" ? t.width : 60) : e, 0);
}
function Is(e) {
	return Ts(e).reduce((e, t) => t.orientation === "top" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
function Ls(e) {
	return Ts(e).reduce((e, t) => t.orientation === "bottom" && !t.mirror && !t.hide ? e + t.height : e, 0);
}
var Rs = B([
	xs,
	Ss,
	ws,
	Ns,
	Ps,
	Fs,
	Is,
	Ls,
	Vr,
	Hr
], (e, t, n, r, i, a, o, s, c, l) => {
	var u = {
		left: (n.left || 0) + i,
		right: (n.right || 0) + a
	}, d = ks(ks({}, {
		top: (n.top || 0) + o,
		bottom: (n.bottom || 0) + s
	}), u), f = d.bottom;
	d.bottom += r, d = rs(d, c, l);
	var p = e - d.left - d.right, m = t - d.top - d.bottom;
	return ks(ks({ brushBottom: f }, d), {}, {
		width: Math.max(p, 0),
		height: Math.max(m, 0)
	});
}), zs = B(Rs, (e) => ({
	x: e.left,
	y: e.top,
	width: e.width,
	height: e.height
})), Bs = B(xs, Ss, (e, t) => ({
	x: 0,
	y: 0,
	width: e,
	height: t
})), Vs = /*#__PURE__*/ (0, C.createContext)(null), Hs = () => (0, C.useContext)(Vs) != null, Us = (e) => e.brush, Ws = B([
	Us,
	Rs,
	ws
], (e, t, n) => ({
	height: e.height,
	x: I(e.x) ? e.x : t.left,
	y: I(e.y) ? e.y : t.top + t.height + t.brushBottom - ((n == null ? void 0 : n.bottom) || 0),
	width: I(e.width) ? e.width : t.width
}));
//#endregion
//#region node_modules/es-toolkit/dist/function/debounce.mjs
function Gs(e, t, { signal: n, edges: r } = {}) {
	let i, a = null, o = r != null && r.includes("leading"), s = r == null || r.includes("trailing"), c = () => {
		a !== null && (e.apply(i, a), i = void 0, a = null);
	}, l = () => {
		s && c(), p();
	}, u = null, d = () => {
		u != null && clearTimeout(u), u = setTimeout(() => {
			u = null, l();
		}, t);
	}, f = () => {
		u !== null && (clearTimeout(u), u = null);
	}, p = () => {
		f(), i = void 0, a = null;
	}, m = () => {
		c();
	}, h = function(...e) {
		if (n != null && n.aborted) return;
		i = this, a = e;
		let t = u == null;
		d(), o && t && c();
	};
	return h.schedule = d, h.cancel = p, h.flush = m, n == null || n.addEventListener("abort", p, { once: !0 }), h;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/function/debounce.mjs
function Ks(e, t = 0, n = {}) {
	typeof n != "object" && (n = {});
	let { leading: r = !1, trailing: i = !0, maxWait: a } = n, o = [, ,];
	r && (o[0] = "leading"), i && (o[1] = "trailing");
	let s, c = null, l = Gs(function(...t) {
		s = e.apply(this, t), c = null;
	}, t, { edges: o }), u = function(...t) {
		return a != null && (c === null && (c = Date.now()), Date.now() - c >= a) ? (s = e.apply(this, t), c = Date.now(), l.cancel(), l.schedule(), s) : (l.apply(this, t), s);
	};
	return u.cancel = l.cancel, u.flush = () => (l.flush(), s), u;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/function/throttle.mjs
function qs(e, t = 0, n = {}) {
	let { leading: r = !0, trailing: i = !0 } = n;
	return Ks(e, t, {
		leading: r,
		maxWait: t,
		trailing: i
	});
}
//#endregion
//#region node_modules/recharts/es6/util/LogUtils.js
var Js = function(e, t) {
	var n = [...arguments].slice(2);
	if (typeof console < "u" && console.warn && (t === void 0 && console.warn("LogUtils requires an error message argument"), !e)) if (t === void 0) console.warn("Minified exception occurred; use the non-minified dev environment for the full error message and additional helpful warnings.");
	else {
		var r = 0;
		console.warn(t.replace(/%s/g, () => n[r++]));
	}
}, Ys = {
	width: "100%",
	height: "100%",
	debounce: 0,
	minWidth: 0,
	initialDimension: {
		width: -1,
		height: -1
	}
}, Xs = (e, t, n) => {
	var r = n.width, i = r === void 0 ? Ys.width : r, a = n.height, o = a === void 0 ? Ys.height : a, s = n.aspect, c = n.maxHeight, l = kt(i) ? e : Number(i), u = kt(o) ? t : Number(o);
	return s && s > 0 && (l ? u = l / s : u && (l = u * s), c && u != null && u > c && (u = c)), {
		calculatedWidth: l,
		calculatedHeight: u
	};
}, Zs = {
	width: 0,
	height: 0,
	overflow: "visible"
}, Qs = {
	width: 0,
	overflowX: "visible"
}, $s = {
	height: 0,
	overflowY: "visible"
}, ec = {}, tc = (e) => {
	var t = e.width, n = e.height, r = kt(t), i = kt(n);
	return r && i ? Zs : r ? Qs : i ? $s : ec;
};
function nc(e) {
	var t = e.width, n = e.height, r = e.aspect, i = t, a = n;
	return i === void 0 && a === void 0 ? (i = Ys.width, a = Ys.height) : i === void 0 ? i = r && r > 0 ? void 0 : Ys.width : a === void 0 && (a = r && r > 0 ? void 0 : Ys.height), {
		width: i,
		height: a
	};
}
//#endregion
//#region node_modules/recharts/es6/component/ResponsiveContainer.js
var rc = [
	"aspect",
	"initialDimension",
	"width",
	"height",
	"minWidth",
	"minHeight",
	"maxHeight",
	"children",
	"debounce",
	"id",
	"className",
	"onResize",
	"style"
];
function ic() {
	return ic = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, ic.apply(null, arguments);
}
function ac(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function oc(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? ac(Object(n), !0).forEach(function(t) {
			sc(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : ac(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function sc(e, t, n) {
	return (t = cc(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function cc(e) {
	var t = lc(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function lc(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function uc(e, t) {
	return hc(e) || mc(e, t) || fc(e, t) || dc();
}
function dc() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function fc(e, t) {
	if (e) {
		if (typeof e == "string") return pc(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? pc(e, t) : void 0;
	}
}
function pc(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function mc(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function hc(e) {
	if (Array.isArray(e)) return e;
}
function J(e, t) {
	if (e == null) return {};
	var n, r, i = gc(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function gc(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var _c = /*#__PURE__*/ (0, C.createContext)(Ys.initialDimension);
function vc(e) {
	return Xo(e.width) && Xo(e.height);
}
function yc(e) {
	var t = e.children, n = e.width, r = e.height, i = (0, C.useMemo)(() => ({
		width: n,
		height: r
	}), [n, r]);
	return vc(i) ? /*#__PURE__*/ C.createElement(_c.Provider, { value: i }, t) : null;
}
var bc = () => (0, C.useContext)(_c), xc = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.aspect, r = e.initialDimension, i = r === void 0 ? Ys.initialDimension : r, a = e.width, o = e.height, s = e.minWidth, c = s === void 0 ? Ys.minWidth : s, l = e.minHeight, u = e.maxHeight, d = e.children, f = e.debounce, p = f === void 0 ? Ys.debounce : f, m = e.id, h = e.className, g = e.onResize, _ = e.style, v = _ === void 0 ? {} : _, y = J(e, rc), b = (0, C.useRef)(null), x = (0, C.useRef)();
	x.current = g, (0, C.useImperativeHandle)(t, () => b.current);
	var S = uc((0, C.useState)({
		containerWidth: i.width,
		containerHeight: i.height
	}), 2), w = S[0], T = S[1], E = (0, C.useCallback)((e, t) => {
		T((n) => {
			var r = Math.round(e), i = Math.round(t);
			return n.containerWidth === r && n.containerHeight === i ? n : {
				containerWidth: r,
				containerHeight: i
			};
		});
	}, []);
	(0, C.useEffect)(() => {
		if (b.current == null || typeof ResizeObserver > "u") return Bt;
		var e = (e) => {
			var t, n = e[0];
			if (n != null) {
				var r = n.contentRect, i = r.width, a = r.height;
				E(i, a), (t = x.current) == null || t.call(x, i, a);
			}
		};
		p > 0 && (e = qs(e, p, {
			trailing: !0,
			leading: !1
		}));
		var t = new ResizeObserver(e), n = b.current.getBoundingClientRect(), r = n.width, i = n.height;
		return E(r, i), t.observe(b.current), () => {
			t.disconnect();
		};
	}, [E, p]);
	var D = w.containerWidth, O = w.containerHeight;
	Js(!n || n > 0, "The aspect(%s) must be greater than zero.", n);
	var k = Xs(D, O, {
		width: a,
		height: o,
		aspect: n,
		maxHeight: u
	}), A = k.calculatedWidth, j = k.calculatedHeight;
	return Js(D < 0 || O < 0 || A != null && A > 0 || j != null && j > 0, "The width(%s) and height(%s) of chart should be greater than 0,\n       please check the style of container, or the props width(%s) and height(%s),\n       or add a minWidth(%s) or minHeight(%s) or use aspect(%s) to control the\n       height and width.", A, j, a, o, c, l, n), /*#__PURE__*/ C.createElement("div", ic({
		id: m ? `${m}` : void 0,
		className: N("recharts-responsive-container", h),
		style: oc(oc({}, v), {}, {
			width: a,
			height: o,
			minWidth: c,
			minHeight: l,
			maxHeight: u
		}),
		ref: b
	}, y), /*#__PURE__*/ C.createElement("div", { style: tc({
		width: a,
		height: o
	}) }, /*#__PURE__*/ C.createElement(yc, {
		width: A,
		height: j
	}, d)));
}), Sc = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = bc();
	if (Xo(n.width) && Xo(n.height)) return e.children;
	var r = nc({
		width: e.width,
		height: e.height,
		aspect: e.aspect
	}), i = r.width, a = r.height, o = Xs(void 0, void 0, {
		width: i,
		height: a,
		aspect: e.aspect,
		maxHeight: e.maxHeight
	}), s = o.calculatedWidth, c = o.calculatedHeight;
	return I(s) && I(c) ? /*#__PURE__*/ C.createElement(yc, {
		width: s,
		height: c
	}, e.children) : /*#__PURE__*/ C.createElement(xc, ic({}, e, {
		width: i,
		height: a,
		ref: t
	}));
});
//#endregion
//#region node_modules/recharts/es6/context/chartLayoutContext.js
function Cc(e) {
	if (e) return {
		x: e.x,
		y: e.y,
		upperWidth: "upperWidth" in e ? e.upperWidth : e.width,
		lowerWidth: "lowerWidth" in e ? e.lowerWidth : e.width,
		width: e.width,
		height: e.height
	};
}
var wc = () => {
	var e, t = Hs(), n = z(zs), r = z(Ws), i = (e = z(Us)) == null ? void 0 : e.padding;
	return !t || !r || !i ? n : {
		width: r.width - i.left - i.right,
		height: r.height - i.top - i.bottom,
		x: i.left,
		y: i.top
	};
}, Tc = {
	top: 0,
	bottom: 0,
	left: 0,
	right: 0,
	width: 0,
	height: 0,
	brushBottom: 0
}, Ec = () => {
	var e;
	return (e = z(Rs)) == null ? Tc : e;
}, Dc = () => z(xs), Oc = () => z(Ss), Y = (e) => e.layout.layoutType, kc = () => z(Y), Ac = () => {
	var e = kc();
	if (e === "horizontal" || e === "vertical") return e;
}, jc = (e) => {
	var t = e.layout.layoutType;
	if (t === "centric" || t === "radial") return t;
}, Mc = () => kc() !== void 0, Nc = (e) => {
	var t = R(), n = Hs(), r = e.width, i = e.height, a = bc(), o = r, s = i;
	return a && (o = a.width > 0 ? a.width : r, s = a.height > 0 ? a.height : i), (0, C.useEffect)(() => {
		!n && Xo(o) && Xo(s) && t(Ko({
			width: o,
			height: s
		}));
	}, [
		t,
		n,
		o,
		s
	]), null;
}, Pc = eo({
	name: "legend",
	initialState: {
		settings: {
			layout: "horizontal",
			align: "center",
			verticalAlign: "bottom",
			itemSorter: "value"
		},
		size: {
			width: 0,
			height: 0
		},
		payload: []
	},
	reducers: {
		setLegendSize(e, t) {
			e.size.width = t.payload.width, e.size.height = t.payload.height;
		},
		setLegendSettings(e, t) {
			e.settings.align = t.payload.align, e.settings.layout = t.payload.layout, e.settings.verticalAlign = t.payload.verticalAlign, e.settings.itemSorter = t.payload.itemSorter;
		},
		addLegendPayload: {
			reducer(e, t) {
				e.payload.push(W(t.payload));
			},
			prepare: G()
		},
		replaceLegendPayload: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ea(e).payload.indexOf(W(r));
				a > -1 && (e.payload[a] = W(i));
			},
			prepare: G()
		},
		removeLegendPayload: {
			reducer(e, t) {
				var n = Ea(e).payload.indexOf(W(t.payload));
				n > -1 && e.payload.splice(n, 1);
			},
			prepare: G()
		}
	}
}), Fc = Pc.actions;
Fc.setLegendSize, Fc.setLegendSettings;
var Ic = Fc.addLegendPayload, Lc = Fc.replaceLegendPayload, Rc = Fc.removeLegendPayload, zc = Pc.reducer, Bc = /* @__PURE__ */ o(((e) => {
	var t = d();
	t.useSyncExternalStore, t.useRef, t.useEffect, t.useMemo, t.useDebugValue;
}));
(/* @__PURE__ */ o(((e, t) => {
	t.exports = Bc();
})))();
function Vc(e) {
	e();
}
function Hc() {
	let e = null, t = null;
	return {
		clear() {
			e = null, t = null;
		},
		notify() {
			Vc(() => {
				let t = e;
				for (; t;) t.callback(), t = t.next;
			});
		},
		get() {
			let t = [], n = e;
			for (; n;) t.push(n), n = n.next;
			return t;
		},
		subscribe(n) {
			let r = !0, i = t = {
				callback: n,
				next: null,
				prev: t
			};
			return i.prev ? i.prev.next = i : e = i, function() {
				!r || e === null || (r = !1, i.next ? i.next.prev = i.prev : t = i.prev, i.prev ? i.prev.next = i.next : e = i.next);
			};
		}
	};
}
var Uc = {
	notify() {},
	get: () => []
};
function X(e, t) {
	let n, r = Uc, i = 0, a = !1;
	function o(e) {
		u();
		let t = r.subscribe(e), n = !1;
		return () => {
			n || (n = !0, t(), d());
		};
	}
	function s() {
		r.notify();
	}
	function c() {
		m.onStateChange && m.onStateChange();
	}
	function l() {
		return a;
	}
	function u() {
		i++, n || (n = t ? t.addNestedSub(c) : e.subscribe(c), r = Hc());
	}
	function d() {
		i--, n && i === 0 && (n(), n = void 0, r.clear(), r = Uc);
	}
	function f() {
		a || (a = !0, u());
	}
	function p() {
		a && (a = !1, d());
	}
	let m = {
		addNestedSub: o,
		notifyNestedSubs: s,
		handleChangeWrapper: c,
		isSubscribed: l,
		trySubscribe: f,
		tryUnsubscribe: p,
		getListeners: () => r
	};
	return m;
}
var Wc = typeof window < "u" && window.document !== void 0 && window.document.createElement !== void 0, Gc = typeof navigator < "u" && navigator.product === "ReactNative", Kc = Wc || Gc ? C.useLayoutEffect : C.useEffect;
function qc(e, t) {
	return e === t ? e !== 0 || t !== 0 || 1 / e == 1 / t : e !== e && t !== t;
}
function Jc(e, t) {
	if (qc(e, t)) return !0;
	if (typeof e != "object" || !e || typeof t != "object" || !t) return !1;
	let n = Object.keys(e), r = Object.keys(t);
	if (n.length !== r.length) return !1;
	for (let r = 0; r < n.length; r++) if (!Object.prototype.hasOwnProperty.call(t, n[r]) || !qc(e[n[r]], t[n[r]])) return !1;
	return !0;
}
var Yc = /* @__PURE__ */ Symbol.for("react-redux-context"), Xc = typeof globalThis < "u" ? globalThis : {};
function Zc() {
	var e;
	if (!C.createContext) return {};
	let t = (e = Xc[Yc]) == null ? Xc[Yc] = /* @__PURE__ */ new Map() : e, n = t.get(C.createContext);
	return n || (n = C.createContext(null), t.set(C.createContext, n)), n;
}
var Qc = /* @__PURE__ */ Zc();
function $c(e) {
	let { children: t, context: n, serverState: r, store: i } = e, a = C.useMemo(() => {
		let e = X(i);
		return {
			store: i,
			subscription: e,
			getServerState: r ? () => r : void 0
		};
	}, [i, r]), o = C.useMemo(() => i.getState(), [i]);
	Kc(() => {
		let { subscription: e } = a;
		return e.onStateChange = e.notifyNestedSubs, e.trySubscribe(), o !== i.getState() && e.notifyNestedSubs(), () => {
			e.tryUnsubscribe(), e.onStateChange = void 0;
		};
	}, [a, o]);
	let s = n || Qc;
	return /* @__PURE__ */ C.createElement(s.Provider, { value: a }, t);
}
var el = $c, tl = /* @__PURE__ */ new Set([
	"axisLine",
	"tickLine",
	"activeBar",
	"activeDot",
	"activeLabel",
	"activeShape",
	"allowEscapeViewBox",
	"background",
	"cursor",
	"dot",
	"label",
	"line",
	"margin",
	"padding",
	"position",
	"shape",
	"style",
	"tick",
	"wrapperStyle",
	"radius",
	"throttledEvents"
]);
function nl(e, t) {
	return e == null && t == null ? !0 : typeof e == "number" && typeof t == "number" ? e === t || e !== e && t !== t : e === t;
}
function rl(e, t) {
	for (var n of /* @__PURE__ */ new Set([...Object.keys(e), ...Object.keys(t)])) if (tl.has(n)) {
		if (e[n] == null && t[n] == null) continue;
		if (!Jc(e[n], t[n])) return !1;
	} else if (!nl(e[n], t[n])) return !1;
	return !0;
}
//#endregion
//#region node_modules/recharts/es6/component/DefaultTooltipContent.js
function il() {
	return il = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, il.apply(null, arguments);
}
function al(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ol(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? al(Object(n), !0).forEach(function(t) {
			sl(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : al(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function sl(e, t, n) {
	return (t = cl(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function cl(e) {
	var t = ll(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ll(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function ul(e, t) {
	return hl(e) || ml(e, t) || fl(e, t) || dl();
}
function dl() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function fl(e, t) {
	if (e) {
		if (typeof e == "string") return pl(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? pl(e, t) : void 0;
	}
}
function pl(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function ml(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function hl(e) {
	if (Array.isArray(e)) return e;
}
function gl(e) {
	return Array.isArray(e) && At(e[0]) && At(e[1]) ? e.join(" ~ ") : e;
}
var _l = {
	separator: " : ",
	contentStyle: {
		margin: 0,
		padding: 10,
		backgroundColor: "#fff",
		border: "1px solid #ccc",
		whiteSpace: "nowrap"
	},
	itemStyle: {
		display: "block",
		paddingTop: 4,
		paddingBottom: 4,
		color: "#000"
	},
	labelStyle: {},
	accessibilityLayer: !1
};
function vl(e, t) {
	return t == null ? e : Br(e, t);
}
var yl = (e) => {
	var t = e.separator, n = t === void 0 ? _l.separator : t, r = e.contentStyle, i = e.itemStyle, a = e.labelStyle, o = a === void 0 ? _l.labelStyle : a, s = e.payload, c = e.formatter, l = e.itemSorter, u = e.wrapperClassName, d = e.labelClassName, f = e.label, p = e.labelFormatter, m = e.accessibilityLayer, h = m === void 0 ? _l.accessibilityLayer : m, g = () => {
		if (s && s.length) {
			var e = {
				padding: 0,
				margin: 0
			}, t = vl(s, l).map((e, t) => {
				if (!e || e.type === "none") return null;
				var r = e.formatter || c || gl, a = e.value, o = e.name, l = a, u = o;
				if (r) {
					var d = r(a, o, e, t, s);
					if (Array.isArray(d)) {
						var f = ul(d, 2);
						l = f[0], u = f[1];
					} else if (d != null) l = d;
					else return null;
				}
				var p = ol(ol({}, _l.itemStyle), {}, { color: e.color || _l.itemStyle.color }, i);
				return /*#__PURE__*/ C.createElement("li", {
					className: "recharts-tooltip-item",
					key: `tooltip-item-${t}`,
					style: p
				}, At(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-name" }, u) : null, At(u) ? /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-separator" }, n) : null, /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-value" }, l), /*#__PURE__*/ C.createElement("span", { className: "recharts-tooltip-item-unit" }, e.unit || ""));
			});
			return /*#__PURE__*/ C.createElement("ul", {
				className: "recharts-tooltip-item-list",
				style: e
			}, t);
		}
		return null;
	}, _ = ol(ol({}, _l.contentStyle), r), v = ol({ margin: 0 }, o), y = !Lt(f), b = y ? f : "", x = N("recharts-default-tooltip", u), S = N("recharts-tooltip-label", d);
	y && p && s != null && (b = p(f, s));
	var w = h ? {
		role: "status",
		"aria-live": "assertive"
	} : {};
	return /*#__PURE__*/ C.createElement("div", il({
		className: x,
		style: _
	}, w), /*#__PURE__*/ C.createElement("p", {
		className: S,
		style: v
	}, /*#__PURE__*/ C.isValidElement(b) ? b : `${b}`), g());
}, bl = "recharts-tooltip-wrapper", xl = { visibility: "hidden" };
function Sl(e) {
	var t = e.coordinate, n = e.translateX, r = e.translateY;
	return N(bl, {
		[`${bl}-right`]: I(n) && t && I(t.x) && n >= t.x,
		[`${bl}-left`]: I(n) && t && I(t.x) && n < t.x,
		[`${bl}-bottom`]: I(r) && t && I(t.y) && r >= t.y,
		[`${bl}-top`]: I(r) && t && I(t.y) && r < t.y
	});
}
function Cl(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.key, i = e.offset, a = e.position, o = e.reverseDirection, s = e.tooltipDimension, c = e.viewBox, l = e.viewBoxDimension;
	if (a && I(a[r])) return a[r];
	var u = n[r] - s - (i > 0 ? i : 0), d = n[r] + i;
	if (t[r]) return o[r] ? u : d;
	var f = c[r];
	return f == null ? 0 : o[r] ? Math.max(u < f ? d : u, f) : l == null ? 0 : d + s > f + l ? Math.max(u, f) : Math.max(d, f);
}
function wl(e) {
	var t = e.translateX, n = e.translateY;
	return { transform: e.useTranslate3d ? `translate3d(${t}px, ${n}px, 0)` : `translate(${t}px, ${n}px)` };
}
function Tl(e) {
	var t = e.allowEscapeViewBox, n = e.coordinate, r = e.offsetTop, i = e.offsetLeft, a = e.position, o = e.reverseDirection, s = e.tooltipBox, c = e.useTranslate3d, l = e.viewBox, u, d, f;
	return s.height > 0 && s.width > 0 && n ? (d = Cl({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "x",
		offset: i,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.width,
		viewBox: l,
		viewBoxDimension: l.width
	}), f = Cl({
		allowEscapeViewBox: t,
		coordinate: n,
		key: "y",
		offset: r,
		position: a,
		reverseDirection: o,
		tooltipDimension: s.height,
		viewBox: l,
		viewBoxDimension: l.height
	}), u = wl({
		translateX: d,
		translateY: f,
		useTranslate3d: c
	})) : u = xl, {
		cssProperties: u,
		cssClasses: Sl({
			translateX: d,
			translateY: f,
			coordinate: n
		})
	};
}
var El = {
	devToolsEnabled: !0,
	isSsr: !(typeof window < "u" && window.document && window.document.createElement && window.setTimeout)
};
//#endregion
//#region node_modules/recharts/es6/util/usePrefersReducedMotion.js
function Dl(e, t) {
	return Ml(e) || jl(e, t) || kl(e, t) || Ol();
}
function Ol() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function kl(e, t) {
	if (e) {
		if (typeof e == "string") return Al(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Al(e, t) : void 0;
	}
}
function Al(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function jl(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Ml(e) {
	if (Array.isArray(e)) return e;
}
function Nl() {
	var e = Dl((0, C.useState)(() => El.isSsr || !window.matchMedia ? !1 : window.matchMedia("(prefers-reduced-motion: reduce)").matches), 2), t = e[0], n = e[1];
	return (0, C.useEffect)(() => {
		if (window.matchMedia) {
			var e = window.matchMedia("(prefers-reduced-motion: reduce)"), t = () => {
				n(e.matches);
			};
			return e.addEventListener("change", t), () => {
				e.removeEventListener("change", t);
			};
		}
	}, []), t;
}
//#endregion
//#region node_modules/recharts/es6/component/TooltipBoundingBox.js
function Pl(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Fl(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Pl(Object(n), !0).forEach(function(t) {
			Il(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Pl(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Il(e, t, n) {
	return (t = Ll(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ll(e) {
	var t = Rl(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Rl(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function zl(e, t) {
	return Wl(e) || Ul(e, t) || Vl(e, t) || Bl();
}
function Bl() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Vl(e, t) {
	if (e) {
		if (typeof e == "string") return Hl(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Hl(e, t) : void 0;
	}
}
function Hl(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Ul(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Wl(e) {
	if (Array.isArray(e)) return e;
}
function Gl(e) {
	if (!(e.prefersReducedMotion && e.isAnimationActive === "auto") && e.isAnimationActive && e.active) {
		var t = typeof e.animationEasing == "string" ? e.animationEasing : "ease";
		return `transform ${e.animationDuration}ms ${t}`;
	}
}
function Kl(e) {
	var t, n, r, i, a, o, s = Nl(), c = zl(C.useState(() => ({
		dismissed: !1,
		dismissedAtCoordinate: {
			x: 0,
			y: 0
		}
	})), 2), l = c[0], u = c[1];
	C.useEffect(() => {
		var t = (t) => {
			if (t.key === "Escape") {
				var n, r, i, a;
				u({
					dismissed: !0,
					dismissedAtCoordinate: {
						x: (n = (r = e.coordinate) == null ? void 0 : r.x) == null ? 0 : n,
						y: (i = (a = e.coordinate) == null ? void 0 : a.y) == null ? 0 : i
					}
				});
			}
		};
		return document.addEventListener("keydown", t), () => {
			document.removeEventListener("keydown", t);
		};
	}, [(t = e.coordinate) == null ? void 0 : t.x, (n = e.coordinate) == null ? void 0 : n.y]), l.dismissed && (((r = (i = e.coordinate) == null ? void 0 : i.x) == null ? 0 : r) !== l.dismissedAtCoordinate.x || ((a = (o = e.coordinate) == null ? void 0 : o.y) == null ? 0 : a) !== l.dismissedAtCoordinate.y) && u(Fl(Fl({}, l), {}, { dismissed: !1 }));
	var d = Tl({
		allowEscapeViewBox: e.allowEscapeViewBox,
		coordinate: e.coordinate,
		offsetLeft: typeof e.offset == "number" ? e.offset : e.offset.x,
		offsetTop: typeof e.offset == "number" ? e.offset : e.offset.y,
		position: e.position,
		reverseDirection: e.reverseDirection,
		tooltipBox: {
			height: e.lastBoundingBox.height,
			width: e.lastBoundingBox.width
		},
		useTranslate3d: e.useTranslate3d,
		viewBox: e.viewBox
	}), f = d.cssClasses, p = d.cssProperties, m = Fl(Fl({}, e.hasPortalFromProps ? {} : Fl(Fl({ transition: Gl({
		prefersReducedMotion: s,
		isAnimationActive: e.isAnimationActive,
		active: e.active,
		animationDuration: e.animationDuration,
		animationEasing: e.animationEasing
	}) }, p), {}, {
		pointerEvents: "none",
		position: "absolute",
		top: 0,
		left: 0
	})), {}, { visibility: !l.dismissed && e.active && e.hasPayload ? "visible" : "hidden" }, e.wrapperStyle);
	return /*#__PURE__*/ C.createElement("div", {
		xmlns: "http://www.w3.org/1999/xhtml",
		tabIndex: -1,
		className: f,
		style: m,
		ref: e.innerRef
	}, e.children);
}
var ql = /*#__PURE__*/ C.memo(Kl), Jl = () => {
	var e;
	return (e = z((e) => e.rootProps.accessibilityLayer)) == null || e;
};
//#endregion
//#region node_modules/recharts/es6/shape/Curve.js
function Yl() {
	return Yl = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Yl.apply(null, arguments);
}
function Xl(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Zl(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Xl(Object(n), !0).forEach(function(t) {
			Ql(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Xl(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ql(e, t, n) {
	return (t = $l(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function $l(e) {
	var t = eu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function eu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var tu = {
	curveBasisClosed: He,
	curveBasisOpen: We,
	curveBasis: Be,
	curveBumpX: Fe,
	curveBumpY: Ie,
	curveLinearClosed: Ke,
	curveLinear: ke,
	curveMonotoneX: et,
	curveMonotoneY: tt,
	curveNatural: it,
	curveStep: ot,
	curveStepAfter: ct,
	curveStepBefore: st
}, nu = (e) => q(e.x) && q(e.y), ru = (e) => e.base != null && nu(e.base) && nu(e), iu = (e) => e.x, au = (e) => e.y, ou = (e, t) => {
	if (typeof e == "function") return e;
	var n = `curve${Rt(e)}`;
	if ((n === "curveMonotone" || n === "curveBump") && t) {
		var r = tu[`${n}${t === "vertical" ? "Y" : "X"}`];
		if (r) return r;
	}
	return tu[n] || ke;
}, su = {
	connectNulls: !1,
	type: "linear"
}, cu = (e) => {
	var t = e.type, n = t === void 0 ? su.type : t, r = e.points, i = r === void 0 ? [] : r, a = e.baseLine, o = e.layout, s = e.connectNulls, c = s === void 0 ? su.connectNulls : s, l = ou(n, o), u = c ? i.filter(nu) : i;
	if (Array.isArray(a)) {
		var d, f = i.map((e, t) => Zl(Zl({}, e), {}, { base: a[t] }));
		return d = o === "vertical" ? Ne().y(au).x1(iu).x0((e) => e.base.x) : Ne().x(iu).y1(au).y0((e) => e.base.y), d.defined(ru).curve(l)(c ? f.filter(ru) : f);
	}
	return (o === "vertical" && I(a) ? Ne().y(au).x1(iu).x0(a) : I(a) ? Ne().x(iu).y1(au).y0(a) : Me().x(iu).y(au)).defined(nu).curve(l)(u);
}, lu = (e) => {
	var t = e.className, n = e.points, r = e.path, i = e.pathRef, a = kc();
	if ((!n || !n.length) && !r) return null;
	var o = {
		type: e.type,
		points: e.points,
		baseLine: e.baseLine,
		layout: e.layout || a,
		connectNulls: e.connectNulls
	}, s = n && n.length ? cu(o) : r;
	return /*#__PURE__*/ C.createElement("path", Yl({}, F(e), Ht(e), {
		className: N("recharts-curve", t),
		d: s === null ? void 0 : s,
		ref: i
	}));
}, uu = [
	"x",
	"y",
	"top",
	"left",
	"width",
	"height",
	"className"
];
function du() {
	return du = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, du.apply(null, arguments);
}
function fu(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function pu(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? fu(Object(n), !0).forEach(function(t) {
			mu(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : fu(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function mu(e, t, n) {
	return (t = hu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function hu(e) {
	var t = gu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function gu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function _u(e, t) {
	if (e == null) return {};
	var n, r, i = vu(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function vu(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var yu = (e, t, n, r, i, a) => `M${e},${i}v${r}M${a},${t}h${n}`, bu = (e) => {
	var t = e.x, n = t === void 0 ? 0 : t, r = e.y, i = r === void 0 ? 0 : r, a = e.top, o = a === void 0 ? 0 : a, s = e.left, c = s === void 0 ? 0 : s, l = e.width, u = l === void 0 ? 0 : l, d = e.height, f = d === void 0 ? 0 : d, p = e.className, m = _u(e, uu), h = pu({
		x: n,
		y: i,
		top: o,
		left: c,
		width: u,
		height: f
	}, m);
	return !I(n) || !I(i) || !I(u) || !I(f) || !I(o) || !I(c) ? null : /*#__PURE__*/ C.createElement("path", du({}, ae(h), {
		className: N("recharts-cross", p),
		d: yu(n, i, u, f, o, c)
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorRectangle.js
function xu(e, t, n, r) {
	var i = r / 2;
	return {
		stroke: "none",
		fill: "#ccc",
		x: e === "horizontal" ? t.x - i : n.left + .5,
		y: e === "horizontal" ? n.top + .5 : t.y - i,
		width: e === "horizontal" ? r : n.width - 1,
		height: e === "horizontal" ? n.height - 1 : r
	};
}
var Su = (e, t) => [
	0,
	3 * e,
	3 * t - 6 * e,
	3 * e - 3 * t + 1
], Cu = (e, t) => e.map((e, n) => e * t ** n).reduce((e, t) => e + t), wu = (e, t) => (n) => Cu(Su(e, t), n), Tu = (e, t) => (n) => Cu([...Su(e, t).map((e, t) => e * t).slice(1), 0], n), Eu = (e) => {
	var t, n = e.split("(");
	if (n.length !== 2 || n[0] !== "cubic-bezier") return null;
	var r = (t = n[1]) == null || (t = t.split(")")[0]) == null ? void 0 : t.split(",");
	if (r == null || r.length !== 4) return null;
	var i = r.map((e) => parseFloat(e));
	return [
		i[0],
		i[1],
		i[2],
		i[3]
	];
}, Du = function() {
	var e = [...arguments];
	if (e.length === 1) switch (e[0]) {
		case "linear": return [
			0,
			0,
			1,
			1
		];
		case "ease": return [
			.25,
			.1,
			.25,
			1
		];
		case "ease-in": return [
			.42,
			0,
			1,
			1
		];
		case "ease-out": return [
			.42,
			0,
			.58,
			1
		];
		case "ease-in-out": return [
			0,
			0,
			.58,
			1
		];
		default:
			var t = Eu(e[0]);
			if (t) return t;
	}
	return e.length === 4 ? e : [
		0,
		0,
		1,
		1
	];
}, Ou = (e, t, n, r) => {
	var i = wu(e, n), a = wu(t, r), o = Tu(e, n), s = (e) => e > 1 ? 1 : e < 0 ? 0 : e, c = (e) => {
		for (var t = e > 1 ? 1 : e, n = t, r = 0; r < 8; ++r) {
			var c = i(n) - t, l = o(n);
			if (Math.abs(c - t) < 1e-4 || l < 1e-4) return a(n);
			n = s(n - c / l);
		}
		return a(n);
	};
	return c.isStepper = !1, c;
}, ku = function() {
	return Ou(...Du(...arguments));
}, Au = function() {
	for (var e = arguments.length > 0 && arguments[0] !== void 0 ? arguments[0] : {}, t = e.stiff, n = t === void 0 ? 100 : t, r = e.damping, i = r === void 0 ? 8 : r, a = e.dt, o = a === void 0 ? 16.67 : a, s = 1, c = [0], l = 0, u = 0, d = 1e4, f = 0; f < d;) {
		var p = -(l - s) * n, m = u * i;
		if (u += (p - m) * o / 1e3, l += u * o / 1e3, c.push(l), Math.abs(l - s) < 1e-4 && Math.abs(u) < 1e-4) break;
		f++;
	}
	c[c.length - 1] = s;
	var h = c.length - 1;
	return (e) => {
		var t, n, r;
		if (e <= 0) return 0;
		if (e >= 1) return s;
		var i = e * h, a = Math.floor(i), o = i - a;
		return ((t = c[a]) == null ? 0 : t) + (((n = c[a + 1]) == null ? 0 : n) - ((r = c[a]) == null ? 0 : r)) * o;
	};
}, ju = (e) => {
	if (typeof e == "string") switch (e) {
		case "ease":
		case "ease-in-out":
		case "ease-out":
		case "ease-in":
		case "linear": return ku(e);
		case "spring": return Au();
		default: if (e.split("(")[0] === "cubic-bezier") return ku(e);
	}
	return typeof e == "function" ? e : null;
}, Mu = /*#__PURE__*/ (0, C.createContext)((e, t, n) => {
	var r, i = (a) => {
		var o = t.tick(a);
		if (t.getState() === "active") {
			if (n(t.getInterpolated()), t.getProgress() === 1) {
				t.complete(), r = void 0;
				return;
			}
			r = e.setTimeout(i, o);
			return;
		}
		r = e.setTimeout(i, o);
	};
	return r = e.setTimeout(i, 0), () => {
		var e;
		return (e = r) == null ? void 0 : e();
	};
});
Mu.Provider;
function Nu(e) {
	var t = (0, C.useContext)(Mu);
	return (0, C.useMemo)(() => e == null ? t : e, [e, t]);
}
//#endregion
//#region node_modules/recharts/es6/animation/AnimationHandle.js
function Pu(e, t, n) {
	return (t = Fu(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Fu(e) {
	var t = Iu(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Iu(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var Lu = "init", Ru = "pending", zu = "active", Bu = "completed";
function Vu(e) {
	return Math.max(0, e);
}
var Hu = class {
	getAnimationStartedTime() {
		return this.animationStartedTime;
	}
	getBeginStartedTime() {
		return this.beginStartedTime;
	}
	constructor(e) {
		var t;
		Pu(this, "state", Lu), this.animationId = e.animationId, this.onAnimationEnd = e.onAnimationEnd, this.animationDuration = Vu(e.animationDuration), this.animationBegin = Vu(e.animationBegin), this.progress = 0, this.from = e.from, this.to = e.to, this.easing = e.easing, (t = e.onAnimationStart) == null || t.call(e);
	}
	getState() {
		return this.state;
	}
	getEasing() {
		return this.easing;
	}
	getAnimationDuration() {
		return this.animationDuration;
	}
	tick(e) {
		if (this.getState() === Lu) return this.state = Ru, this.beginStartedTime = e, this.animationBegin;
		if (this.getState() === Ru) {
			if (this.beginStartedTime == null) throw Error();
			var t = e - this.beginStartedTime;
			return t >= this.animationBegin ? (this.state = zu, this.animationStartedTime = e, this.nextAnimationUpdate(0)) : Vu(this.animationBegin - t);
		}
		if (this.getState() === zu) {
			if (this.animationStartedTime == null) throw Error();
			var n = e - this.animationStartedTime;
			return this.setProgress(n / this.animationDuration), this.nextAnimationUpdate(n);
		}
		return 0;
	}
	setProgress(e) {
		this.progress = Math.min(1, Math.max(0, e));
	}
	getProgress() {
		return this.progress;
	}
	complete() {
		if (this.progress = 1, this.state === "active") {
			var e;
			(e = this.onAnimationEnd) == null || e.call(this);
		}
		this.state = Bu;
	}
	getFrom() {
		return this.from;
	}
	getTo() {
		return this.to;
	}
	getAnimationId() {
		return this.animationId;
	}
	getAnimationBegin() {
		return this.animationBegin;
	}
}, Uu = class extends Hu {
	nextAnimationUpdate() {
		return 0;
	}
	getInterpolated() {
		return this.easing(Ft(this.getFrom(), this.getTo(), this.getProgress()));
	}
}, Wu = class {
	setTimeout(e) {
		var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0, n = performance.now(), r = null, i = (a) => {
			a - n >= t ? e(a) : r = requestAnimationFrame(i);
		};
		return r = requestAnimationFrame(i), () => {
			r != null && cancelAnimationFrame(r);
		};
	}
};
//#endregion
//#region node_modules/recharts/es6/animation/JavascriptAnimate.js
function Gu(e, t) {
	return Xu(e) || Yu(e, t) || qu(e, t) || Ku();
}
function Ku() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function qu(e, t) {
	if (e) {
		if (typeof e == "string") return Ju(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Ju(e, t) : void 0;
	}
}
function Ju(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Yu(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Xu(e) {
	if (Array.isArray(e)) return e;
}
var Zu = {
	begin: 0,
	duration: 1e3,
	easing: "ease",
	isActive: !0,
	canBegin: !0,
	onAnimationEnd: () => {},
	onAnimationStart: () => {}
}, Qu = 0, $u = 1;
function ed(e) {
	var t = Yt(e, Zu), n = t.animationId, r = t.isActive, i = t.canBegin, a = t.duration, o = t.easing, s = t.begin, c = t.onAnimationEnd, l = t.onAnimationStart, u = t.children, d = Nl(), f = r === "auto" ? !El.isSsr && !d : r, p = Nu(t.animationController), m = Gu((0, C.useState)(f ? Qu : $u), 2), h = m[0], g = m[1];
	return (0, C.useEffect)(() => {
		f || g($u);
	}, [f]), (0, C.useEffect)(() => {
		var e = ju(o);
		return !f || !i || e == null ? Bt : p(new Wu(), new Uu({
			animationId: n,
			easing: e,
			animationDuration: a,
			animationBegin: s,
			onAnimationStart: l,
			onAnimationEnd: c,
			from: Qu,
			to: $u
		}), g);
	}, [
		p,
		n,
		f,
		i,
		a,
		o,
		s,
		l,
		c
	]), u(Number(h));
}
//#endregion
//#region node_modules/recharts/es6/util/useAnimationId.js
function td(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "animation-", n = (0, C.useRef)(Mt(t)), r = (0, C.useRef)(e);
	return r.current !== e && (n.current = Mt(t), r.current = e), n.current;
}
//#endregion
//#region node_modules/recharts/es6/animation/util.js
var nd = (e) => e.replace(/([A-Z])/g, (e) => `-${e.toLowerCase()}`), rd = (e, t, n) => e.map((e) => `${nd(e)} ${t}ms ${n}`).join(","), id = ["radius"], ad = ["radius"], od, sd, cd, ld, ud, dd, fd, pd, md, hd;
function gd(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function _d(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? gd(Object(n), !0).forEach(function(t) {
			vd(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : gd(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function vd(e, t, n) {
	return (t = yd(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function yd(e) {
	var t = bd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function bd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function xd() {
	return xd = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, xd.apply(null, arguments);
}
function Sd(e, t) {
	if (e == null) return {};
	var n, r, i = Cd(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Cd(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function wd(e, t) {
	return kd(e) || Od(e, t) || Ed(e, t) || Td();
}
function Td() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Ed(e, t) {
	if (e) {
		if (typeof e == "string") return Dd(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Dd(e, t) : void 0;
	}
}
function Dd(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Od(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function kd(e) {
	if (Array.isArray(e)) return e;
}
function Ad(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var jd = (e, t, n, r, i) => {
	var a = Tt(n), o = Tt(r), s = Math.min(Math.abs(a) / 2, Math.abs(o) / 2), c = o >= 0 ? 1 : -1, l = a >= 0 ? 1 : -1, u = +(o >= 0 && a >= 0 || o < 0 && a < 0), d;
	if (s > 0 && Array.isArray(i)) {
		for (var f = [
			0,
			0,
			0,
			0
		], p = 0, m = 4; p < m; p++) {
			var h, g = (h = i[p]) == null ? 0 : h;
			f[p] = g > s ? s : g;
		}
		d = Et(od || (od = Ad([
			"M",
			",",
			""
		])), e, t + c * f[0]), f[0] > 0 && (d += Et(sd || (sd = Ad([
			"A ",
			",",
			",0,0,",
			",",
			",",
			""
		])), f[0], f[0], u, e + l * f[0], t)), d += Et(cd || (cd = Ad([
			"L ",
			",",
			""
		])), e + n - l * f[1], t), f[1] > 0 && (d += Et(ld || (ld = Ad([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[1], f[1], u, e + n, t + c * f[1])), d += Et(ud || (ud = Ad([
			"L ",
			",",
			""
		])), e + n, t + r - c * f[2]), f[2] > 0 && (d += Et(dd || (dd = Ad([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[2], f[2], u, e + n - l * f[2], t + r)), d += Et(fd || (fd = Ad([
			"L ",
			",",
			""
		])), e + l * f[3], t + r), f[3] > 0 && (d += Et(pd || (pd = Ad([
			"A ",
			",",
			",0,0,",
			",\n        ",
			",",
			""
		])), f[3], f[3], u, e, t + r - c * f[3])), d += "Z";
	} else if (s > 0 && i === +i && i > 0) {
		var _ = Math.min(s, i);
		d = Et(md || (md = Ad(/* @__PURE__ */ "M .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,.\n            L .,.\n            A .,.,0,0,.,.,. Z".split("."))), e, t + c * _, _, _, u, e + l * _, t, e + n - l * _, t, _, _, u, e + n, t + c * _, e + n, t + r - c * _, _, _, u, e + n - l * _, t + r, e + l * _, t + r, _, _, u, e, t + r - c * _);
	} else d = Et(hd || (hd = Ad([
		"M ",
		",",
		" h ",
		" v ",
		" h ",
		" Z"
	])), e, t, n, r, -n);
	return d;
}, Md = {
	x: 0,
	y: 0,
	width: 0,
	height: 0,
	radius: 0,
	isAnimationActive: !1,
	isUpdateAnimationActive: !1,
	animationBegin: 0,
	animationDuration: 1500,
	animationEasing: "ease"
}, Nd = (e) => {
	var t = Yt(e, Md), n = (0, C.useRef)(null), r = wd((0, C.useState)(-1), 2), i = r[0], a = r[1];
	(0, C.useEffect)(() => {
		if (n.current && n.current.getTotalLength) try {
			var e = n.current.getTotalLength();
			e && a(e);
		} catch (e) {}
	}, []);
	var o = t.x, s = t.y, c = t.width, l = t.height, u = t.radius, d = t.className, f = t.animationEasing, p = t.animationDuration, m = t.animationBegin, h = t.isAnimationActive, g = t.isUpdateAnimationActive, _ = (0, C.useRef)(c), v = (0, C.useRef)(l), y = (0, C.useRef)(o), b = (0, C.useRef)(s), x = td((0, C.useMemo)(() => ({
		x: o,
		y: s,
		width: c,
		height: l,
		radius: u
	}), [
		o,
		s,
		c,
		l,
		u
	]), "rectangle-");
	if (o !== +o || s !== +s || c !== +c || l !== +l || c === 0 || l === 0) return null;
	var S = N("recharts-rectangle", d);
	if (!g) {
		var w = ae(t);
		w.radius;
		var T = Sd(w, id);
		return /*#__PURE__*/ C.createElement("path", xd({}, T, {
			x: Tt(o),
			y: Tt(s),
			width: Tt(c),
			height: Tt(l),
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: jd(o, s, c, l, u)
		}));
	}
	var E = _.current, D = v.current, O = y.current, k = b.current, A = `0px ${i === -1 ? 1 : i}px`, j = `${i}px ${i}px`, M = rd(["strokeDasharray"], p, typeof f == "string" ? f : Md.animationEasing);
	return /*#__PURE__*/ C.createElement(ed, {
		animationId: x,
		key: x,
		canBegin: i > 0,
		duration: p,
		easing: f,
		isActive: g,
		begin: m
	}, (e) => {
		var r = Ft(E, c, e), i = Ft(D, l, e), a = Ft(O, o, e), d = Ft(k, s, e);
		n.current && (_.current = r, v.current = i, y.current = a, b.current = d);
		var f = h ? e > 0 ? {
			transition: M,
			strokeDasharray: j
		} : { strokeDasharray: A } : { strokeDasharray: j }, p = ae(t);
		p.radius;
		var m = Sd(p, ad);
		return /*#__PURE__*/ C.createElement("path", xd({}, m, {
			radius: typeof u == "number" ? u : void 0,
			className: S,
			d: jd(a, d, r, i, u),
			ref: n,
			style: _d(_d({}, f), t.style)
		}));
	});
};
//#endregion
//#region node_modules/recharts/es6/util/PolarUtils.js
function Pd(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Fd(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Pd(Object(n), !0).forEach(function(t) {
			Id(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Pd(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Id(e, t, n) {
	return (t = Ld(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ld(e) {
	var t = Rd(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Rd(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var zd = Math.PI / 180, Bd = (e) => e * 180 / Math.PI, Vd = (e, t, n, r) => ({
	x: e + Math.cos(-zd * r) * n,
	y: t + Math.sin(-zd * r) * n
}), Hd = function(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : {
		top: 0,
		right: 0,
		bottom: 0,
		left: 0,
		width: 0,
		height: 0,
		brushBottom: 0
	};
	return Math.min(Math.abs(e - (n.left || 0) - (n.right || 0)), Math.abs(t - (n.top || 0) - (n.bottom || 0))) / 2;
}, Ud = (e, t) => {
	var n = e.x, r = e.y, i = t.x, a = t.y;
	return Math.sqrt((n - i) ** 2 + (r - a) ** 2);
}, Wd = (e, t) => {
	var n = e.x, r = e.y, i = t.cx, a = t.cy, o = Ud({
		x: n,
		y: r
	}, {
		x: i,
		y: a
	});
	if (o <= 0) return {
		radius: o,
		angle: 0
	};
	var s = (n - i) / o, c = Math.acos(s);
	return r > a && (c = 2 * Math.PI - c), {
		radius: o,
		angle: Bd(c),
		angleInRadian: c
	};
}, Gd = (e) => {
	var t = e.startAngle, n = e.endAngle, r = Math.floor(t / 360), i = Math.floor(n / 360), a = Math.min(r, i);
	return {
		startAngle: t - a * 360,
		endAngle: n - a * 360
	};
}, Kd = (e, t) => {
	var n = t.startAngle, r = t.endAngle, i = Math.floor(n / 360), a = Math.floor(r / 360);
	return e + Math.min(i, a) * 360;
}, qd = (e, t) => {
	var n = e.relativeX, r = e.relativeY, i = Wd({
		x: n,
		y: r
	}, t), a = i.radius, o = i.angle, s = t.innerRadius, c = t.outerRadius;
	if (a < s || a > c || a === 0) return null;
	var l = Gd(t), u = l.startAngle, d = l.endAngle, f = o, p;
	if (u <= d) {
		for (; f > d;) f -= 360;
		for (; f < u;) f += 360;
		p = f >= u && f <= d;
	} else {
		for (; f > u;) f -= 360;
		for (; f < d;) f += 360;
		p = f >= d && f <= u;
	}
	return p ? Fd(Fd({}, t), {}, {
		radius: a,
		angle: Kd(f, t)
	}) : null;
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getRadialCursorPoints.js
function Jd(e) {
	var t = e.cx, n = e.cy, r = e.radius, i = e.startAngle, a = e.endAngle;
	return {
		points: [Vd(t, n, r, i), Vd(t, n, r, a)],
		cx: t,
		cy: n,
		radius: r,
		startAngle: i,
		endAngle: a
	};
}
//#endregion
//#region node_modules/recharts/es6/shape/Sector.js
var Yd, Xd, Zd, Qd, $d, ef, tf;
function nf() {
	return nf = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, nf.apply(null, arguments);
}
function rf(e, t) {
	return t || (t = e.slice(0)), Object.freeze(Object.defineProperties(e, { raw: { value: Object.freeze(t) } }));
}
var af = (e, t) => Dt(t - e) * Math.min(Math.abs(t - e), 359.999), of = (e) => {
	var t = e.cx, n = e.cy, r = e.radius, i = e.angle, a = e.sign, o = e.isExternal, s = e.cornerRadius, c = e.cornerIsExternal, l = s * (o ? 1 : -1) + r, u = Math.asin(s / l) / zd, d = c ? i : i + a * u, f = Vd(t, n, l, d), p = Vd(t, n, r, d), m = c ? i - a * u : i;
	return {
		center: f,
		circleTangency: p,
		lineTangency: Vd(t, n, l * Math.cos(u * zd), m),
		theta: u
	};
}, sf = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.startAngle, o = e.endAngle, s = af(a, o), c = a + s, l = Vd(t, n, i, a), u = Vd(t, n, i, c), d = Et(Yd || (Yd = rf([
		"M ",
		",",
		"\n    A ",
		",",
		",0,\n    ",
		",",
		",\n    ",
		",",
		"\n  "
	])), l.x, l.y, i, i, +(Math.abs(s) > 180), +(a > c), u.x, u.y);
	if (r > 0) {
		var f = Vd(t, n, r, a), p = Vd(t, n, r, c);
		d += Et(Xd || (Xd = rf([
			"L ",
			",",
			"\n            A ",
			",",
			",0,\n            ",
			",",
			",\n            ",
			",",
			" Z"
		])), p.x, p.y, r, r, +(Math.abs(s) > 180), +(a <= c), f.x, f.y);
	} else d += Et(Zd || (Zd = rf([
		"L ",
		",",
		" Z"
	])), t, n);
	return d;
}, cf = (e) => {
	var t = e.cx, n = e.cy, r = e.innerRadius, i = e.outerRadius, a = e.cornerRadius, o = e.forceCornerRadius, s = e.cornerIsExternal, c = e.startAngle, l = e.endAngle, u = Dt(l - c), d = of({
		cx: t,
		cy: n,
		radius: i,
		angle: c,
		sign: u,
		cornerRadius: a,
		cornerIsExternal: s
	}), f = d.circleTangency, p = d.lineTangency, m = d.theta, h = of({
		cx: t,
		cy: n,
		radius: i,
		angle: l,
		sign: -u,
		cornerRadius: a,
		cornerIsExternal: s
	}), g = h.circleTangency, _ = h.lineTangency, v = h.theta, y = s ? Math.abs(c - l) : Math.abs(c - l) - m - v;
	if (y < 0) return o ? Et(Qd || (Qd = rf([
		"M ",
		",",
		"\n        a",
		",",
		",0,0,1,",
		",0\n        a",
		",",
		",0,0,1,",
		",0\n      "
	])), p.x, p.y, a, a, a * 2, a, a, -a * 2) : sf({
		cx: t,
		cy: n,
		innerRadius: r,
		outerRadius: i,
		startAngle: c,
		endAngle: l
	});
	var b = Et($d || ($d = rf([
		"M ",
		",",
		"\n    A",
		",",
		",0,0,",
		",",
		",",
		"\n    A",
		",",
		",0,",
		",",
		",",
		",",
		"\n    A",
		",",
		",0,0,",
		",",
		",",
		"\n  "
	])), p.x, p.y, a, a, +(u < 0), f.x, f.y, i, i, +(y > 180), +(u < 0), g.x, g.y, a, a, +(u < 0), _.x, _.y);
	if (r > 0) {
		var x = of({
			cx: t,
			cy: n,
			radius: r,
			angle: c,
			sign: u,
			isExternal: !0,
			cornerRadius: a,
			cornerIsExternal: s
		}), S = x.circleTangency, C = x.lineTangency, w = x.theta, T = of({
			cx: t,
			cy: n,
			radius: r,
			angle: l,
			sign: -u,
			isExternal: !0,
			cornerRadius: a,
			cornerIsExternal: s
		}), E = T.circleTangency, D = T.lineTangency, O = T.theta, k = s ? Math.abs(c - l) : Math.abs(c - l) - w - O;
		if (k < 0 && a === 0) return `${b}L${t},${n}Z`;
		b += Et(ef || (ef = rf([
			"L",
			",",
			"\n      A",
			",",
			",0,0,",
			",",
			",",
			"\n      A",
			",",
			",0,",
			",",
			",",
			",",
			"\n      A",
			",",
			",0,0,",
			",",
			",",
			"Z"
		])), D.x, D.y, a, a, +(u < 0), E.x, E.y, r, r, +(k > 180), +(u > 0), S.x, S.y, a, a, +(u < 0), C.x, C.y);
	} else b += Et(tf || (tf = rf([
		"L",
		",",
		"Z"
	])), t, n);
	return b;
}, lf = {
	cx: 0,
	cy: 0,
	innerRadius: 0,
	outerRadius: 0,
	startAngle: 0,
	endAngle: 0,
	cornerRadius: 0,
	forceCornerRadius: !1,
	cornerIsExternal: !1
}, uf = (e) => {
	var t = Yt(e, lf), n = t.cx, r = t.cy, i = t.innerRadius, a = t.outerRadius, o = t.cornerRadius, s = t.forceCornerRadius, c = t.cornerIsExternal, l = t.startAngle, u = t.endAngle, d = t.className;
	if (a < i || l === u) return null;
	var f = N("recharts-sector", d), p = a - i, m = Nt(o, p, 0, !0), h = m > 0 && Math.abs(l - u) < 360 ? cf({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		cornerRadius: Math.min(m, p / 2),
		forceCornerRadius: s,
		cornerIsExternal: c,
		startAngle: l,
		endAngle: u
	}) : sf({
		cx: n,
		cy: r,
		innerRadius: i,
		outerRadius: a,
		startAngle: l,
		endAngle: u
	});
	return /*#__PURE__*/ C.createElement("path", nf({}, ae(t), {
		className: f,
		d: h
	}));
};
//#endregion
//#region node_modules/recharts/es6/util/cursor/getCursorPoints.js
function df(e, t, n) {
	if (e === "horizontal") return [{
		x: t.x,
		y: n.top
	}, {
		x: t.x,
		y: n.top + n.height
	}];
	if (e === "vertical") return [{
		x: n.left,
		y: t.y
	}, {
		x: n.left + n.width,
		y: t.y
	}];
	if (Vt(t)) {
		if (e === "centric") {
			var r = t.cx, i = t.cy, a = t.innerRadius, o = t.outerRadius, s = t.angle, c = Vd(r, i, a, s), l = Vd(r, i, o, s);
			return [{
				x: c.x,
				y: c.y
			}, {
				x: l.x,
				y: l.y
			}];
		}
		return Jd(t);
	}
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toNumber.mjs
function ff(e) {
	return Fr(e) ? NaN : Number(e);
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/util/toFinite.mjs
function pf(e) {
	return e ? (e = ff(e), e === Infinity || e === -Infinity ? (e < 0 ? -1 : 1) * Number.MAX_VALUE : e === e ? e : 0) : e === 0 ? e : 0;
}
//#endregion
//#region node_modules/es-toolkit/dist/compat/math/range.mjs
function mf(e, t, n) {
	n && typeof n != "number" && Mr(e, t, n) && (t = n = void 0), e = pf(e), t === void 0 ? (t = e, e = 0) : t = pf(t), n = n === void 0 ? e < t ? 1 : -1 : pf(n);
	let r = Math.max(Math.ceil((t - e) / (n || 1)), 0), i = Array(r);
	for (let t = 0; t < r; t++) i[t] = e, e += n;
	return i;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/dataSelectors.js
var hf = (e) => e.chartData, gf = B([hf], (e) => {
	var t = e.chartData == null ? 0 : e.chartData.length - 1;
	return {
		chartData: e.chartData,
		computedData: e.computedData,
		dataEndIndex: t,
		dataStartIndex: 0
	};
}), _f = (e, t, n, r) => r ? gf(e) : hf(e), vf = (e, t, n) => n ? gf(e) : hf(e), yf = B([_f], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
B([gf], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
var bf = B([hf], (e) => {
	var t = e.chartData, n = e.dataStartIndex, r = e.dataEndIndex;
	return t == null ? [] : t.slice(n, r + 1);
});
//#endregion
//#region node_modules/recharts/es6/util/isDomainSpecifiedByUser.js
function xf(e, t) {
	return Ef(e) || Tf(e, t) || Cf(e, t) || Sf();
}
function Sf() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Cf(e, t) {
	if (e) {
		if (typeof e == "string") return wf(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? wf(e, t) : void 0;
	}
}
function wf(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Tf(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Ef(e) {
	if (Array.isArray(e)) return e;
}
function Df(e) {
	if (Array.isArray(e) && e.length === 2) {
		var t = xf(e, 2), n = t[0], r = t[1];
		if (q(n) && q(r)) return !0;
	}
	return !1;
}
function Of(e, t, n) {
	return n ? e : [Math.min(e[0], t[0]), Math.max(e[1], t[1])];
}
function kf(e, t) {
	if (t && typeof e != "function" && Array.isArray(e) && e.length === 2) {
		var n = xf(e, 2), r = n[0], i = n[1], a, o;
		if (q(r)) a = r;
		else if (typeof r == "function") return;
		if (q(i)) o = i;
		else if (typeof i == "function") return;
		var s = [a, o];
		if (Df(s)) return s;
	}
}
function Af(e, t, n) {
	if (!(!n && t == null)) {
		if (typeof e == "function" && t != null) try {
			var r = e(t, n);
			if (Df(r)) return Of(r, t, n);
		} catch (e) {}
		if (Array.isArray(e) && e.length === 2) {
			var i = xf(e, 2), a = i[0], o = i[1], s, c;
			if (a === "auto") t != null && (s = Math.min(...t));
			else if (I(a)) s = a;
			else if (typeof a == "function") try {
				t != null && (s = a(t == null ? void 0 : t[0]));
			} catch (e) {}
			else if (typeof a == "string" && ms.test(a)) {
				var l = ms.exec(a);
				if (l == null || l[1] == null || t == null) s = void 0;
				else {
					var u = +l[1];
					s = t[0] - u;
				}
			} else s = t == null ? void 0 : t[0];
			if (o === "auto") t != null && (c = Math.max(...t));
			else if (I(o)) c = o;
			else if (typeof o == "function") try {
				t != null && (c = o(t == null ? void 0 : t[1]));
			} catch (e) {}
			else if (typeof o == "string" && hs.test(o)) {
				var d = hs.exec(o);
				if (d == null || d[1] == null || t == null) c = void 0;
				else {
					var f = +d[1];
					c = t[1] + f;
				}
			} else c = t == null ? void 0 : t[1];
			var p = [s, c];
			if (Df(p)) return t == null ? p : Of(p, t, n);
		}
	}
}
//#endregion
//#region node_modules/recharts/es6/util/scale/util/arithmetic.js
var Z = /* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
	(function(e) {
		var n = 1e9, r = {
			precision: 20,
			rounding: 4,
			toExpNeg: -7,
			toExpPos: 21,
			LN10: "2.302585092994045684017991454684364207601101488628772976033327900967572609677352480235997205089598298341967784042286"
		}, i = !0, a = "[DecimalError] ", o = a + "Invalid argument: ", s = a + "Exponent out of range: ", c = Math.floor, l = Math.pow, u = /^(\d+(\.\d*)?|\.\d+)(e[+-]?\d+)?$/i, d, f = 1e7, p = 7, m = 9007199254740991, h = c(m / p), g = {};
		g.absoluteValue = g.abs = function() {
			var e = new this.constructor(this);
			return e.s && (e.s = 1), e;
		}, g.comparedTo = g.cmp = function(e) {
			var t, n, r, i, a = this;
			if (e = new a.constructor(e), a.s !== e.s) return a.s || -e.s;
			if (a.e !== e.e) return a.e > e.e ^ a.s < 0 ? 1 : -1;
			for (r = a.d.length, i = e.d.length, t = 0, n = r < i ? r : i; t < n; ++t) if (a.d[t] !== e.d[t]) return a.d[t] > e.d[t] ^ a.s < 0 ? 1 : -1;
			return r === i ? 0 : r > i ^ a.s < 0 ? 1 : -1;
		}, g.decimalPlaces = g.dp = function() {
			var e = this, t = e.d.length - 1, n = (t - e.e) * p;
			if (t = e.d[t], t) for (; t % 10 == 0; t /= 10) n--;
			return n < 0 ? 0 : n;
		}, g.dividedBy = g.div = function(e) {
			return b(this, new this.constructor(e));
		}, g.dividedToIntegerBy = g.idiv = function(e) {
			var t = this, n = t.constructor;
			return D(b(t, new n(e), 0, 1), n.precision);
		}, g.equals = g.eq = function(e) {
			return !this.cmp(e);
		}, g.exponent = function() {
			return S(this);
		}, g.greaterThan = g.gt = function(e) {
			return this.cmp(e) > 0;
		}, g.greaterThanOrEqualTo = g.gte = function(e) {
			return this.cmp(e) >= 0;
		}, g.isInteger = g.isint = function() {
			return this.e > this.d.length - 2;
		}, g.isNegative = g.isneg = function() {
			return this.s < 0;
		}, g.isPositive = g.ispos = function() {
			return this.s > 0;
		}, g.isZero = function() {
			return this.s === 0;
		}, g.lessThan = g.lt = function(e) {
			return this.cmp(e) < 0;
		}, g.lessThanOrEqualTo = g.lte = function(e) {
			return this.cmp(e) < 1;
		}, g.logarithm = g.log = function(e) {
			var t, n = this, r = n.constructor, o = r.precision, s = o + 5;
			if (e === void 0) e = new r(10);
			else if (e = new r(e), e.s < 1 || e.eq(d)) throw Error(a + "NaN");
			if (n.s < 1) throw Error(a + (n.s ? "NaN" : "-Infinity"));
			return n.eq(d) ? new r(0) : (i = !1, t = b(T(n, s), T(e, s), s), i = !0, D(t, o));
		}, g.minus = g.sub = function(e) {
			var t = this;
			return e = new t.constructor(e), t.s == e.s ? O(t, e) : _(t, (e.s = -e.s, e));
		}, g.modulo = g.mod = function(e) {
			var t, n = this, r = n.constructor, o = r.precision;
			if (e = new r(e), !e.s) throw Error(a + "NaN");
			return n.s ? (i = !1, t = b(n, e, 0, 1).times(e), i = !0, n.minus(t)) : D(new r(n), o);
		}, g.naturalExponential = g.exp = function() {
			return x(this);
		}, g.naturalLogarithm = g.ln = function() {
			return T(this);
		}, g.negated = g.neg = function() {
			var e = new this.constructor(this);
			return e.s = -e.s || 0, e;
		}, g.plus = g.add = function(e) {
			var t = this;
			return e = new t.constructor(e), t.s == e.s ? _(t, e) : O(t, (e.s = -e.s, e));
		}, g.precision = g.sd = function(e) {
			var t, n, r, i = this;
			if (e !== void 0 && e !== !!e && e !== 1 && e !== 0) throw Error(o + e);
			if (t = S(i) + 1, r = i.d.length - 1, n = r * p + 1, r = i.d[r], r) {
				for (; r % 10 == 0; r /= 10) n--;
				for (r = i.d[0]; r >= 10; r /= 10) n++;
			}
			return e && t > n ? t : n;
		}, g.squareRoot = g.sqrt = function() {
			var e, t, n, r, o, s, l, u = this, d = u.constructor;
			if (u.s < 1) {
				if (!u.s) return new d(0);
				throw Error(a + "NaN");
			}
			for (e = S(u), i = !1, o = Math.sqrt(+u), o == 0 || o == Infinity ? (t = y(u.d), (t.length + e) % 2 == 0 && (t += "0"), o = Math.sqrt(t), e = c((e + 1) / 2) - (e < 0 || e % 2), o == Infinity ? t = "5e" + e : (t = o.toExponential(), t = t.slice(0, t.indexOf("e") + 1) + e), r = new d(t)) : r = new d(o.toString()), n = d.precision, o = l = n + 3;;) if (s = r, r = s.plus(b(u, s, l + 2)).times(.5), y(s.d).slice(0, l) === (t = y(r.d)).slice(0, l)) {
				if (t = t.slice(l - 3, l + 1), o == l && t == "4999") {
					if (D(s, n + 1, 0), s.times(s).eq(u)) {
						r = s;
						break;
					}
				} else if (t != "9999") break;
				l += 4;
			}
			return i = !0, D(r, n);
		}, g.times = g.mul = function(e) {
			var t, n, r, a, o, s, c, l, u, d = this, p = d.constructor, m = d.d, h = (e = new p(e)).d;
			if (!d.s || !e.s) return new p(0);
			for (e.s *= d.s, n = d.e + e.e, l = m.length, u = h.length, l < u && (o = m, m = h, h = o, s = l, l = u, u = s), o = [], s = l + u, r = s; r--;) o.push(0);
			for (r = u; --r >= 0;) {
				for (t = 0, a = l + r; a > r;) c = o[a] + h[r] * m[a - r - 1] + t, o[a--] = c % f | 0, t = c / f | 0;
				o[a] = (o[a] + t) % f | 0;
			}
			for (; !o[--s];) o.pop();
			return t ? ++n : o.shift(), e.d = o, e.e = n, i ? D(e, p.precision) : e;
		}, g.toDecimalPlaces = g.todp = function(e, t) {
			var r = this, i = r.constructor;
			return r = new i(r), e === void 0 ? r : (v(e, 0, n), t === void 0 ? t = i.rounding : v(t, 0, 8), D(r, e + S(r) + 1, t));
		}, g.toExponential = function(e, t) {
			var r, i = this, a = i.constructor;
			return e === void 0 ? r = k(i, !0) : (v(e, 0, n), t === void 0 ? t = a.rounding : v(t, 0, 8), i = D(new a(i), e + 1, t), r = k(i, !0, e + 1)), r;
		}, g.toFixed = function(e, t) {
			var r, i, a = this, o = a.constructor;
			return e === void 0 ? k(a) : (v(e, 0, n), t === void 0 ? t = o.rounding : v(t, 0, 8), i = D(new o(a), e + S(a) + 1, t), r = k(i.abs(), !1, e + S(i) + 1), a.isneg() && !a.isZero() ? "-" + r : r);
		}, g.toInteger = g.toint = function() {
			var e = this, t = e.constructor;
			return D(new t(e), S(e) + 1, t.rounding);
		}, g.toNumber = function() {
			return +this;
		}, g.toPower = g.pow = function(e) {
			var t, n, r, o, s, l, u = this, f = u.constructor, h = 12, g = +(e = new f(e));
			if (!e.s) return new f(d);
			if (u = new f(u), !u.s) {
				if (e.s < 1) throw Error(a + "Infinity");
				return u;
			}
			if (u.eq(d)) return u;
			if (r = f.precision, e.eq(d)) return D(u, r);
			if (t = e.e, n = e.d.length - 1, l = t >= n, s = u.s, !l) {
				if (s < 0) throw Error(a + "NaN");
			} else if ((n = g < 0 ? -g : g) <= m) {
				for (o = new f(d), t = Math.ceil(r / p + 4), i = !1; n % 2 && (o = o.times(u), A(o.d, t)), n = c(n / 2), n !== 0;) u = u.times(u), A(u.d, t);
				return i = !0, e.s < 0 ? new f(d).div(o) : D(o, r);
			}
			return s = s < 0 && e.d[Math.max(t, n)] & 1 ? -1 : 1, u.s = 1, i = !1, o = e.times(T(u, r + h)), i = !0, o = x(o), o.s = s, o;
		}, g.toPrecision = function(e, t) {
			var r, i, a = this, o = a.constructor;
			return e === void 0 ? (r = S(a), i = k(a, r <= o.toExpNeg || r >= o.toExpPos)) : (v(e, 1, n), t === void 0 ? t = o.rounding : v(t, 0, 8), a = D(new o(a), e, t), r = S(a), i = k(a, e <= r || r <= o.toExpNeg, e)), i;
		}, g.toSignificantDigits = g.tosd = function(e, t) {
			var r = this, i = r.constructor;
			return e === void 0 ? (e = i.precision, t = i.rounding) : (v(e, 1, n), t === void 0 ? t = i.rounding : v(t, 0, 8)), D(new i(r), e, t);
		}, g.toString = g.valueOf = g.val = g.toJSON = function() {
			var e = this, t = S(e), n = e.constructor;
			return k(e, t <= n.toExpNeg || t >= n.toExpPos);
		};
		function _(e, t) {
			var n, r, a, o, s, c, l, u, d = e.constructor, m = d.precision;
			if (!e.s || !t.s) return t.s || (t = new d(e)), i ? D(t, m) : t;
			if (l = e.d, u = t.d, s = e.e, a = t.e, l = l.slice(), o = s - a, o) {
				for (o < 0 ? (r = l, o = -o, c = u.length) : (r = u, a = s, c = l.length), s = Math.ceil(m / p), c = s > c ? s + 1 : c + 1, o > c && (o = c, r.length = 1), r.reverse(); o--;) r.push(0);
				r.reverse();
			}
			for (c = l.length, o = u.length, c - o < 0 && (o = c, r = u, u = l, l = r), n = 0; o;) n = (l[--o] = l[o] + u[o] + n) / f | 0, l[o] %= f;
			for (n && (l.unshift(n), ++a), c = l.length; l[--c] == 0;) l.pop();
			return t.d = l, t.e = a, i ? D(t, m) : t;
		}
		function v(e, t, n) {
			if (e !== ~~e || e < t || e > n) throw Error(o + e);
		}
		function y(e) {
			var t, n, r, i = e.length - 1, a = "", o = e[0];
			if (i > 0) {
				for (a += o, t = 1; t < i; t++) r = e[t] + "", n = p - r.length, n && (a += w(n)), a += r;
				o = e[t], r = o + "", n = p - r.length, n && (a += w(n));
			} else if (o === 0) return "0";
			for (; o % 10 == 0;) o /= 10;
			return a + o;
		}
		var b = (function() {
			function e(e, t) {
				var n, r = 0, i = e.length;
				for (e = e.slice(); i--;) n = e[i] * t + r, e[i] = n % f | 0, r = n / f | 0;
				return r && e.unshift(r), e;
			}
			function t(e, t, n, r) {
				var i, a;
				if (n != r) a = n > r ? 1 : -1;
				else for (i = a = 0; i < n; i++) if (e[i] != t[i]) {
					a = e[i] > t[i] ? 1 : -1;
					break;
				}
				return a;
			}
			function n(e, t, n) {
				for (var r = 0; n--;) e[n] -= r, r = +(e[n] < t[n]), e[n] = r * f + e[n] - t[n];
				for (; !e[0] && e.length > 1;) e.shift();
			}
			return function(r, i, o, s) {
				var c, l, u, d, m, h, g, _, v, y, b, x, C, w, T, E, O, k, A = r.constructor, j = r.s == i.s ? 1 : -1, M = r.d, N = i.d;
				if (!r.s) return new A(r);
				if (!i.s) throw Error(a + "Division by zero");
				for (l = r.e - i.e, O = N.length, T = M.length, g = new A(j), _ = g.d = [], u = 0; N[u] == (M[u] || 0);) ++u;
				if (N[u] > (M[u] || 0) && --l, x = o == null ? o = A.precision : s ? o + (S(r) - S(i)) + 1 : o, x < 0) return new A(0);
				if (x = x / p + 2 | 0, u = 0, O == 1) for (d = 0, N = N[0], x++; (u < T || d) && x--; u++) C = d * f + (M[u] || 0), _[u] = C / N | 0, d = C % N | 0;
				else {
					for (d = f / (N[0] + 1) | 0, d > 1 && (N = e(N, d), M = e(M, d), O = N.length, T = M.length), w = O, v = M.slice(0, O), y = v.length; y < O;) v[y++] = 0;
					k = N.slice(), k.unshift(0), E = N[0], N[1] >= f / 2 && ++E;
					do
						d = 0, c = t(N, v, O, y), c < 0 ? (b = v[0], O != y && (b = b * f + (v[1] || 0)), d = b / E | 0, d > 1 ? (d >= f && (d = f - 1), m = e(N, d), h = m.length, y = v.length, c = t(m, v, h, y), c == 1 && (d--, n(m, O < h ? k : N, h))) : (d == 0 && (c = d = 1), m = N.slice()), h = m.length, h < y && m.unshift(0), n(v, m, y), c == -1 && (y = v.length, c = t(N, v, O, y), c < 1 && (d++, n(v, O < y ? k : N, y))), y = v.length) : c === 0 && (d++, v = [0]), _[u++] = d, c && v[0] ? v[y++] = M[w] || 0 : (v = [M[w]], y = 1);
					while ((w++ < T || v[0] !== void 0) && x--);
				}
				return _[0] || _.shift(), g.e = l, D(g, s ? o + S(g) + 1 : o);
			};
		})();
		function x(e, t) {
			var n, r, a, o, c, u, f = 0, p = 0, m = e.constructor, h = m.precision;
			if (S(e) > 16) throw Error(s + S(e));
			if (!e.s) return new m(d);
			for (t == null ? (i = !1, u = h) : u = t, c = new m(.03125); e.abs().gte(.1);) e = e.times(c), p += 5;
			for (r = Math.log(l(2, p)) / Math.LN10 * 2 + 5 | 0, u += r, n = a = o = new m(d), m.precision = u;;) {
				if (a = D(a.times(e), u), n = n.times(++f), c = o.plus(b(a, n, u)), y(c.d).slice(0, u) === y(o.d).slice(0, u)) {
					for (; p--;) o = D(o.times(o), u);
					return m.precision = h, t == null ? (i = !0, D(o, h)) : o;
				}
				o = c;
			}
		}
		function S(e) {
			for (var t = e.e * p, n = e.d[0]; n >= 10; n /= 10) t++;
			return t;
		}
		function C(e, t, n) {
			if (t > e.LN10.sd()) throw i = !0, n && (e.precision = n), Error(a + "LN10 precision limit exceeded");
			return D(new e(e.LN10), t);
		}
		function w(e) {
			for (var t = ""; e--;) t += "0";
			return t;
		}
		function T(e, t) {
			var n, r, o, s, c, l, u, f, p, m = 1, h = 10, g = e, _ = g.d, v = g.constructor, x = v.precision;
			if (g.s < 1) throw Error(a + (g.s ? "NaN" : "-Infinity"));
			if (g.eq(d)) return new v(0);
			if (t == null ? (i = !1, f = x) : f = t, g.eq(10)) return t == null && (i = !0), C(v, f);
			if (f += h, v.precision = f, n = y(_), r = n.charAt(0), s = S(g), Math.abs(s) < 0x5543df729c000) {
				for (; r < 7 && r != 1 || r == 1 && n.charAt(1) > 3;) g = g.times(e), n = y(g.d), r = n.charAt(0), m++;
				s = S(g), r > 1 ? (g = new v("0." + n), s++) : g = new v(r + "." + n.slice(1));
			} else return u = C(v, f + 2, x).times(s + ""), g = T(new v(r + "." + n.slice(1)), f - h).plus(u), v.precision = x, t == null ? (i = !0, D(g, x)) : g;
			for (l = c = g = b(g.minus(d), g.plus(d), f), p = D(g.times(g), f), o = 3;;) {
				if (c = D(c.times(p), f), u = l.plus(b(c, new v(o), f)), y(u.d).slice(0, f) === y(l.d).slice(0, f)) return l = l.times(2), s !== 0 && (l = l.plus(C(v, f + 2, x).times(s + ""))), l = b(l, new v(m), f), v.precision = x, t == null ? (i = !0, D(l, x)) : l;
				l = u, o += 2;
			}
		}
		function E(e, t) {
			var n, r, a;
			for ((n = t.indexOf(".")) > -1 && (t = t.replace(".", "")), (r = t.search(/e/i)) > 0 ? (n < 0 && (n = r), n += +t.slice(r + 1), t = t.substring(0, r)) : n < 0 && (n = t.length), r = 0; t.charCodeAt(r) === 48;) ++r;
			for (a = t.length; t.charCodeAt(a - 1) === 48;) --a;
			if (t = t.slice(r, a), t) {
				if (a -= r, n = n - r - 1, e.e = c(n / p), e.d = [], r = (n + 1) % p, n < 0 && (r += p), r < a) {
					for (r && e.d.push(+t.slice(0, r)), a -= p; r < a;) e.d.push(+t.slice(r, r += p));
					t = t.slice(r), r = p - t.length;
				} else r -= a;
				for (; r--;) t += "0";
				if (e.d.push(+t), i && (e.e > h || e.e < -h)) throw Error(s + n);
			} else e.s = 0, e.e = 0, e.d = [0];
			return e;
		}
		function D(e, t, n) {
			var r, a, o, u, d, m, g, _, v = e.d;
			for (u = 1, o = v[0]; o >= 10; o /= 10) u++;
			if (r = t - u, r < 0) r += p, a = t, g = v[_ = 0];
			else {
				if (_ = Math.ceil((r + 1) / p), o = v.length, _ >= o) return e;
				for (g = o = v[_], u = 1; o >= 10; o /= 10) u++;
				r %= p, a = r - p + u;
			}
			if (n !== void 0 && (o = l(10, u - a - 1), d = g / o % 10 | 0, m = t < 0 || v[_ + 1] !== void 0 || g % o, m = n < 4 ? (d || m) && (n == 0 || n == (e.s < 0 ? 3 : 2)) : d > 5 || d == 5 && (n == 4 || m || n == 6 && (r > 0 ? a > 0 ? g / l(10, u - a) : 0 : v[_ - 1]) % 10 & 1 || n == (e.s < 0 ? 8 : 7))), t < 1 || !v[0]) return m ? (o = S(e), v.length = 1, t = t - o - 1, v[0] = l(10, (p - t % p) % p), e.e = c(-t / p) || 0) : (v.length = 1, v[0] = e.e = e.s = 0), e;
			if (r == 0 ? (v.length = _, o = 1, _--) : (v.length = _ + 1, o = l(10, p - r), v[_] = a > 0 ? (g / l(10, u - a) % l(10, a) | 0) * o : 0), m) for (;;) if (_ == 0) {
				(v[0] += o) == f && (v[0] = 1, ++e.e);
				break;
			} else {
				if (v[_] += o, v[_] != f) break;
				v[_--] = 0, o = 1;
			}
			for (r = v.length; v[--r] === 0;) v.pop();
			if (i && (e.e > h || e.e < -h)) throw Error(s + S(e));
			return e;
		}
		function O(e, t) {
			var n, r, a, o, s, c, l, u, d, m, h = e.constructor, g = h.precision;
			if (!e.s || !t.s) return t.s ? t.s = -t.s : t = new h(e), i ? D(t, g) : t;
			if (l = e.d, m = t.d, r = t.e, u = e.e, l = l.slice(), s = u - r, s) {
				for (d = s < 0, d ? (n = l, s = -s, c = m.length) : (n = m, r = u, c = l.length), a = Math.max(Math.ceil(g / p), c) + 2, s > a && (s = a, n.length = 1), n.reverse(), a = s; a--;) n.push(0);
				n.reverse();
			} else {
				for (a = l.length, c = m.length, d = a < c, d && (c = a), a = 0; a < c; a++) if (l[a] != m[a]) {
					d = l[a] < m[a];
					break;
				}
				s = 0;
			}
			for (d && (n = l, l = m, m = n, t.s = -t.s), c = l.length, a = m.length - c; a > 0; --a) l[c++] = 0;
			for (a = m.length; a > s;) {
				if (l[--a] < m[a]) {
					for (o = a; o && l[--o] === 0;) l[o] = f - 1;
					--l[o], l[a] += f;
				}
				l[a] -= m[a];
			}
			for (; l[--c] === 0;) l.pop();
			for (; l[0] === 0; l.shift()) --r;
			return l[0] ? (t.d = l, t.e = r, i ? D(t, g) : t) : new h(0);
		}
		function k(e, t, n) {
			var r, i = S(e), a = y(e.d), o = a.length;
			return t ? (n && (r = n - o) > 0 ? a = a.charAt(0) + "." + a.slice(1) + w(r) : o > 1 && (a = a.charAt(0) + "." + a.slice(1)), a = a + (i < 0 ? "e" : "e+") + i) : i < 0 ? (a = "0." + w(-i - 1) + a, n && (r = n - o) > 0 && (a += w(r))) : i >= o ? (a += w(i + 1 - o), n && (r = n - i - 1) > 0 && (a = a + "." + w(r))) : ((r = i + 1) < o && (a = a.slice(0, r) + "." + a.slice(r)), n && (r = n - o) > 0 && (i + 1 === o && (a += "."), a += w(r))), e.s < 0 ? "-" + a : a;
		}
		function A(e, t) {
			if (e.length > t) return e.length = t, !0;
		}
		function j(e) {
			var t, n, r;
			function i(e) {
				var t = this;
				if (!(t instanceof i)) return new i(e);
				if (t.constructor = i, e instanceof i) {
					t.s = e.s, t.e = e.e, t.d = (e = e.d) ? e.slice() : e;
					return;
				}
				if (typeof e == "number") {
					if (e * 0 != 0) throw Error(o + e);
					if (e > 0) t.s = 1;
					else if (e < 0) e = -e, t.s = -1;
					else {
						t.s = 0, t.e = 0, t.d = [0];
						return;
					}
					if (e === ~~e && e < 1e7) {
						t.e = 0, t.d = [e];
						return;
					}
					return E(t, e.toString());
				} else if (typeof e != "string") throw Error(o + e);
				if (e.charCodeAt(0) === 45 ? (e = e.slice(1), t.s = -1) : t.s = 1, u.test(e)) E(t, e);
				else throw Error(o + e);
			}
			if (i.prototype = g, i.ROUND_UP = 0, i.ROUND_DOWN = 1, i.ROUND_CEIL = 2, i.ROUND_FLOOR = 3, i.ROUND_HALF_UP = 4, i.ROUND_HALF_DOWN = 5, i.ROUND_HALF_EVEN = 6, i.ROUND_HALF_CEIL = 7, i.ROUND_HALF_FLOOR = 8, i.clone = j, i.config = i.set = M, e === void 0 && (e = {}), e) for (r = [
				"precision",
				"rounding",
				"toExpNeg",
				"toExpPos",
				"LN10"
			], t = 0; t < r.length;) e.hasOwnProperty(n = r[t++]) || (e[n] = this[n]);
			return i.config(e), i;
		}
		function M(e) {
			if (!e || typeof e != "object") throw Error(a + "Object expected");
			var t, r, i, s = [
				"precision",
				1,
				n,
				"rounding",
				0,
				8,
				"toExpNeg",
				-Infinity,
				0,
				"toExpPos",
				0,
				Infinity
			];
			for (t = 0; t < s.length; t += 3) if ((i = e[r = s[t]]) !== void 0) if (c(i) === i && i >= s[t + 1] && i <= s[t + 2]) this[r] = i;
			else throw Error(o + r + ": " + i);
			if ((i = e[r = "LN10"]) !== void 0) if (i == Math.LN10) this[r] = new this(i);
			else throw Error(o + r + ": " + i);
			return this;
		}
		r = j(r), r.default = r.Decimal = r, d = new r(1), typeof define == "function" && define.amd ? define(function() {
			return r;
		}) : t !== void 0 && t.exports ? t.exports = r : (e || (e = typeof self < "u" && self && self.self == self ? self : Function("return this")()), e.Decimal = r);
	})(e);
})))());
function jf(e) {
	return e === 0 ? 1 : Math.floor(new Z.default(e).abs().log(10).toNumber()) + 1;
}
function Mf(e, t, n) {
	for (var r = new Z.default(e), i = 0, a = []; r.lt(t) && i < 1e5;) a.push(r.toNumber()), r = r.add(n), i++;
	return a;
}
//#endregion
//#region node_modules/recharts/es6/util/scale/getNiceTickValues.js
function Nf(e, t) {
	return Rf(e) || Lf(e, t) || Ff(e, t) || Pf();
}
function Pf() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Ff(e, t) {
	if (e) {
		if (typeof e == "string") return If(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? If(e, t) : void 0;
	}
}
function If(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function Lf(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Rf(e) {
	if (Array.isArray(e)) return e;
}
var zf = (e) => {
	var t = Nf(e, 2), n = t[0], r = t[1], i = n, a = r;
	return n > r && (i = r, a = n), [i, a];
}, Bf = (e, t, n) => {
	if (e.lte(0)) return new Z.default(0);
	var r = jf(e.toNumber()), i = new Z.default(10).pow(r), a = e.div(i), o = r === 1 ? .1 : .05, s = new Z.default(Math.ceil(a.div(o).toNumber())).add(n).mul(o).mul(i);
	return t ? new Z.default(s.toNumber()) : new Z.default(Math.ceil(s.toNumber()));
}, Vf = (e, t, n) => {
	var r;
	if (e.lte(0)) return new Z.default(0);
	var i = [
		1,
		2,
		2.5,
		5
	], a = e.toNumber(), o = Math.floor(new Z.default(a).abs().log(10).toNumber()), s = new Z.default(10).pow(o), c = e.div(s).toNumber(), l = i.findIndex((e) => e >= c - 1e-10);
	if (l === -1 && (s = s.mul(10), l = 0), l += n, l >= i.length) {
		var u = Math.floor(l / i.length);
		l %= i.length, s = s.mul(new Z.default(10).pow(u));
	}
	var d = new Z.default((r = i[l]) == null ? 1 : r).mul(s);
	return t ? d : new Z.default(Math.ceil(d.toNumber()));
}, Hf = (e, t, n) => {
	var r = new Z.default(1), i = new Z.default(e);
	if (!i.isint() && n) {
		var a = Math.abs(e);
		a < 1 ? (r = new Z.default(10).pow(jf(e) - 1), i = new Z.default(Math.floor(i.div(r).toNumber())).mul(r)) : a > 1 && (i = new Z.default(Math.floor(e)));
	} else e === 0 ? i = new Z.default(Math.floor((t - 1) / 2)) : n || (i = new Z.default(Math.floor(e)));
	for (var o = Math.floor((t - 1) / 2), s = [], c = 0; c < t; c++) s.push(i.add(new Z.default(c - o).mul(r)).toNumber());
	return s;
}, Uf = function(e, t, n, r) {
	var i = arguments.length > 4 && arguments[4] !== void 0 ? arguments[4] : 0, a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : Bf;
	if (!Number.isFinite((t - e) / (n - 1))) return {
		step: new Z.default(0),
		tickMin: new Z.default(0),
		tickMax: new Z.default(0)
	};
	var o = a(new Z.default(t).sub(e).div(n - 1), r, i), s;
	e <= 0 && t >= 0 ? s = new Z.default(0) : (s = new Z.default(e).add(t).div(2), s = s.sub(new Z.default(s).mod(o)));
	var c = Math.ceil(s.sub(e).div(o).toNumber()), l = Math.ceil(new Z.default(t).sub(s).div(o).toNumber()), u = c + l + 1;
	return u > n ? Uf(e, t, n, r, i + 1, a) : (u < n && (l = t > 0 ? l + (n - u) : l, c = t > 0 ? c : c + (n - u)), {
		step: o,
		tickMin: s.sub(new Z.default(c).mul(o)),
		tickMax: s.add(new Z.default(l).mul(o))
	});
}, Wf = function(e) {
	var t = Nf(e, 2), n = t[0], r = t[1], i = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 6, a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = Math.max(i, 2), c = Nf(zf([n, r]), 2), l = c[0], u = c[1];
	if (l === -Infinity || u === Infinity) {
		var d = u === Infinity ? [l, ...Array(i - 1).fill(Infinity)] : [...Array(i - 1).fill(-Infinity), u];
		return n > r ? d.reverse() : d;
	}
	if (l === u) return Hf(l, i, a);
	var f = Uf(l, u, s, a, 0, o === "snap125" ? Vf : Bf), p = f.step, m = f.tickMin, h = f.tickMax, g = Mf(m, h.add(new Z.default(.1).mul(p)), p);
	return n > r ? g.reverse() : g;
}, Gf = function(e, t) {
	var n = Nf(e, 2), r = n[0], i = n[1], a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0, o = arguments.length > 3 && arguments[3] !== void 0 ? arguments[3] : "auto", s = Nf(zf([r, i]), 2), c = s[0], l = s[1];
	if (c === -Infinity || l === Infinity) return [r, i];
	if (c === l) return [c];
	var u = o === "snap125" ? Vf : Bf, d = Math.max(t, 2), f = u(new Z.default(l).sub(c).div(d - 1), a, 0), p = [...Mf(new Z.default(c), new Z.default(l), f), l];
	if (a === !1) {
		p = p.map((e) => Math.round(e));
		var m = p.length - 1;
		m > 0 && p[m] === p[m - 1] && (p = p.slice(0, m));
	}
	return r > i ? p.reverse() : p;
}, Kf = (e) => e.rootProps.maxBarSize, qf = (e) => e.rootProps.barGap, Jf = (e) => e.rootProps.barCategoryGap, Yf = (e) => e.rootProps.barSize, Xf = (e) => e.rootProps.stackOffset, Zf = (e) => e.rootProps.reverseStackOrder, Qf = (e) => e.options.chartName, $f = (e) => e.rootProps.syncId, ep = (e) => e.rootProps.syncMethod, tp = (e) => e.options.eventEmitter, np = {
	grid: -100,
	barBackground: -50,
	area: 100,
	cursorRectangle: 200,
	bar: 300,
	line: 400,
	axis: 500,
	scatter: 600,
	activeBar: 1e3,
	cursorLine: 1100,
	activeDot: 1200,
	label: 2e3
}, rp = {
	allowDecimals: !1,
	allowDuplicatedCategory: !0,
	allowDataOverflow: !1,
	angle: 0,
	angleAxisId: 0,
	axisLine: !0,
	axisLineType: "polygon",
	cx: 0,
	cy: 0,
	hide: !1,
	includeHidden: !1,
	label: !1,
	niceTicks: "auto",
	orientation: "outer",
	reversed: !1,
	scale: "auto",
	tick: !0,
	tickLine: !0,
	tickSize: 8,
	type: "auto",
	zIndex: np.axis
}, ip = {
	allowDataOverflow: !1,
	allowDecimals: !1,
	allowDuplicatedCategory: !0,
	angle: 0,
	axisLine: !0,
	includeHidden: !1,
	hide: !1,
	niceTicks: "auto",
	label: !1,
	orientation: "right",
	radiusAxisId: 0,
	reversed: !1,
	scale: "auto",
	stroke: "#ccc",
	tick: !0,
	tickCount: 5,
	tickLine: !0,
	type: "auto",
	zIndex: np.axis
}, ap = (e, t) => {
	if (!(!e || !t)) return e != null && e.reversed ? [t[1], t[0]] : t;
};
//#endregion
//#region node_modules/recharts/es6/util/getAxisTypeBasedOnLayout.js
function op(e, t, n) {
	if (n !== "auto") return n;
	if (e != null) return is(e, t) ? "category" : "number";
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/polarAxisSelectors.js
function sp(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function cp(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? sp(Object(n), !0).forEach(function(t) {
			lp(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : sp(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function lp(e, t, n) {
	return (t = up(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function up(e) {
	var t = dp(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function dp(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var fp = {
	allowDataOverflow: rp.allowDataOverflow,
	allowDecimals: rp.allowDecimals,
	allowDuplicatedCategory: !1,
	dataKey: void 0,
	domain: void 0,
	id: rp.angleAxisId,
	includeHidden: !1,
	name: void 0,
	reversed: rp.reversed,
	scale: rp.scale,
	tick: rp.tick,
	tickCount: void 0,
	ticks: void 0,
	type: rp.type,
	unit: void 0,
	niceTicks: "auto"
}, pp = {
	allowDataOverflow: ip.allowDataOverflow,
	allowDecimals: ip.allowDecimals,
	allowDuplicatedCategory: ip.allowDuplicatedCategory,
	dataKey: void 0,
	domain: void 0,
	id: ip.radiusAxisId,
	includeHidden: ip.includeHidden,
	name: void 0,
	reversed: ip.reversed,
	scale: ip.scale,
	tick: ip.tick,
	tickCount: ip.tickCount,
	ticks: void 0,
	type: ip.type,
	unit: void 0,
	niceTicks: "auto"
}, mp = B([(e, t) => {
	if (t != null) return e.polarAxis.angleAxis[t];
}, jc], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = op(t, "angleAxis", fp.type)) == null ? "category" : n;
	return cp(cp({}, fp), {}, { type: r });
}), hp = B([(e, t) => e.polarAxis.radiusAxis[t], jc], (e, t) => {
	var n;
	if (e != null) return e;
	var r = (n = op(t, "radiusAxis", pp.type)) == null ? "category" : n;
	return cp(cp({}, pp), {}, { type: r });
}), gp = (e) => e.polarOptions, _p = B([
	xs,
	Ss,
	Rs
], Hd), vp = B([gp, _p], (e, t) => {
	if (e != null) return Nt(e.innerRadius, t, 0);
}), yp = B([gp, _p], (e, t) => {
	if (e != null) return Nt(e.outerRadius, t, t * .8);
}), bp = B([gp], (e) => e == null ? [0, 0] : [e.startAngle, e.endAngle]);
B([mp, bp], ap);
var xp = B([
	_p,
	vp,
	yp
], (e, t, n) => {
	if (!(e == null || t == null || n == null)) return [t, n];
});
B([hp, xp], ap);
var Sp = B([
	Y,
	gp,
	vp,
	yp,
	xs,
	Ss
], (e, t, n, r, i, a) => {
	if (!(e !== "centric" && e !== "radial" || t == null || n == null || r == null)) {
		var o = t.cx, s = t.cy, c = t.startAngle, l = t.endAngle;
		return {
			cx: Nt(o, i, i / 2),
			cy: Nt(s, a, a / 2),
			innerRadius: n,
			outerRadius: r,
			startAngle: c,
			endAngle: l,
			clockWise: !1
		};
	}
}), Cp = (e, t) => t, wp = (e, t, n) => n;
//#endregion
//#region node_modules/recharts/es6/util/stacks/getStackSeriesIdentifier.js
function Tp(e) {
	return e == null ? void 0 : e.id;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineDisplayedStackedData.js
function Ep(e, t, n) {
	var r = t.chartData, i = r === void 0 ? [] : r, a = n.allowDuplicatedCategory, o = n.dataKey, s = /* @__PURE__ */ new Map();
	return e.forEach((e) => {
		var t, n = (t = e.data) == null ? i : t;
		if (!(n == null || n.length === 0)) {
			var r = Tp(e);
			n.forEach((t, n) => {
				var i = o == null || a ? n : String(ns(t, o, null)), c = ns(t, e.dataKey, 0), l = s.has(i) ? s.get(i) : {};
				Object.assign(l, { [r]: c }), s.set(i, l);
			});
		}
	}), Array.from(s.values());
}
//#endregion
//#region node_modules/recharts/es6/state/types/StackedGraphicalItem.js
function Dp(e) {
	return "stackId" in e && e.stackId != null && e.dataKey != null;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/numberDomainEqualityCheck.js
var Op = (e, t) => e === t ? !0 : e == null || t == null ? !1 : e[0] === t[0] && e[1] === t[1];
//#endregion
//#region node_modules/recharts/es6/state/selectors/arrayEqualityCheck.js
function kp(e, t) {
	return Array.isArray(e) && Array.isArray(t) && e.length === 0 && t.length === 0 ? !0 : e === t;
}
function Ap(e, t) {
	if (e.length === t.length) {
		for (var n = 0; n < e.length; n++) if (e[n] !== t[n]) return !1;
		return !0;
	}
	return !1;
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectTooltipAxisType.js
var jp = (e) => {
	var t = Y(e);
	return t === "horizontal" ? "xAxis" : t === "vertical" ? "yAxis" : t === "centric" ? "angleAxis" : "radiusAxis";
}, Mp = (e) => e.tooltip.settings.axisId;
//#endregion
//#region node_modules/recharts/es6/util/scale/RechartsScale.js
function Np(e) {
	if (e != null) {
		var t = e.ticks, n = e.bandwidth, r = e.range(), i = [Math.min(...r), Math.max(...r)];
		return {
			domain: () => e.domain(),
			range: function(e) {
				function t() {
					return e.apply(this, arguments);
				}
				return t.toString = function() {
					return e.toString();
				}, t;
			}(() => i),
			rangeMin: () => i[0],
			rangeMax: () => i[1],
			isInRange(e) {
				var t = i[0], n = i[1];
				return t <= n ? e >= t && e <= n : e >= n && e <= t;
			},
			bandwidth: n ? () => n.call(e) : void 0,
			ticks: t ? (n) => t.call(e, n) : void 0,
			map: (t, n) => {
				var r = e(t);
				if (r != null) {
					if (e.bandwidth && n != null && n.position) {
						var i = e.bandwidth();
						switch (n.position) {
							case "middle":
								r += i / 2;
								break;
							case "end":
								r += i;
								break;
							default: break;
						}
					}
					return r;
				}
			}
		};
	}
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineCheckedDomain.js
var Pp = (e, t) => {
	if (t != null) switch (e) {
		case "linear":
			if (!Df(t)) {
				for (var n, r, i = 0; i < t.length; i++) {
					var a = t[i];
					q(a) && ((n === void 0 || a < n) && (n = a), (r === void 0 || a > r) && (r = a));
				}
				return n !== void 0 && r !== void 0 ? [n, r] : void 0;
			}
			return t;
		default: return t;
	}
};
//#endregion
//#region node_modules/d3-array/src/ascending.js
function Fp(e, t) {
	return e == null || t == null ? NaN : e < t ? -1 : e > t ? 1 : e >= t ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/descending.js
function Ip(e, t) {
	return e == null || t == null ? NaN : t < e ? -1 : t > e ? 1 : t >= e ? 0 : NaN;
}
//#endregion
//#region node_modules/d3-array/src/bisector.js
function Lp(e) {
	let t, n, r;
	e.length === 2 ? (t = e === Fp || e === Ip ? e : Rp, n = e, r = e) : (t = Fp, n = (t, n) => Fp(e(t), n), r = (t, n) => e(t) - n);
	function i(e, r, i = 0, a = e.length) {
		if (i < a) {
			if (t(r, r) !== 0) return a;
			do {
				let t = i + a >>> 1;
				n(e[t], r) < 0 ? i = t + 1 : a = t;
			} while (i < a);
		}
		return i;
	}
	function a(e, r, i = 0, a = e.length) {
		if (i < a) {
			if (t(r, r) !== 0) return a;
			do {
				let t = i + a >>> 1;
				n(e[t], r) <= 0 ? i = t + 1 : a = t;
			} while (i < a);
		}
		return i;
	}
	function o(e, t, n = 0, a = e.length) {
		let o = i(e, t, n, a - 1);
		return o > n && r(e[o - 1], t) > -r(e[o], t) ? o - 1 : o;
	}
	return {
		left: i,
		center: o,
		right: a
	};
}
function Rp() {
	return 0;
}
//#endregion
//#region node_modules/d3-array/src/number.js
function zp(e) {
	return e === null ? NaN : +e;
}
function* Bp(e, t) {
	if (t === void 0) for (let t of e) t != null && (t = +t) >= t && (yield t);
	else {
		let n = -1;
		for (let r of e) (r = t(r, ++n, e)) != null && (r = +r) >= r && (yield r);
	}
}
//#endregion
//#region node_modules/d3-array/src/bisect.js
var Vp = Lp(Fp), Hp = Vp.right;
Vp.left, Lp(zp).center;
//#endregion
//#region node_modules/internmap/src/index.js
var Up = class extends Map {
	constructor(e, t = qp) {
		if (super(), Object.defineProperties(this, {
			_intern: { value: /* @__PURE__ */ new Map() },
			_key: { value: t }
		}), e != null) for (let [t, n] of e) this.set(t, n);
	}
	get(e) {
		return super.get(Wp(this, e));
	}
	has(e) {
		return super.has(Wp(this, e));
	}
	set(e, t) {
		return super.set(Gp(this, e), t);
	}
	delete(e) {
		return super.delete(Kp(this, e));
	}
};
function Wp({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : n;
}
function Gp({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) ? e.get(r) : (e.set(r, n), n);
}
function Kp({ _intern: e, _key: t }, n) {
	let r = t(n);
	return e.has(r) && (n = e.get(r), e.delete(r)), n;
}
function qp(e) {
	return typeof e == "object" && e ? e.valueOf() : e;
}
//#endregion
//#region node_modules/d3-array/src/sort.js
function Jp(e = Fp) {
	if (e === Fp) return Yp;
	if (typeof e != "function") throw TypeError("compare is not a function");
	return (t, n) => {
		let r = e(t, n);
		return r || r === 0 ? r : (e(n, n) === 0) - (e(t, t) === 0);
	};
}
function Yp(e, t) {
	return (e == null || !(e >= e)) - (t == null || !(t >= t)) || (e < t ? -1 : +(e > t));
}
//#endregion
//#region node_modules/d3-array/src/ticks.js
var Xp = Math.sqrt(50), Zp = Math.sqrt(10), Qp = Math.sqrt(2);
function $p(e, t, n) {
	let r = (t - e) / Math.max(0, n), i = Math.floor(Math.log10(r)), a = r / 10 ** i, o = a >= Xp ? 10 : a >= Zp ? 5 : a >= Qp ? 2 : 1, s, c, l;
	return i < 0 ? (l = 10 ** -i / o, s = Math.round(e * l), c = Math.round(t * l), s / l < e && ++s, c / l > t && --c, l = -l) : (l = 10 ** i * o, s = Math.round(e / l), c = Math.round(t / l), s * l < e && ++s, c * l > t && --c), c < s && .5 <= n && n < 2 ? $p(e, t, n * 2) : [
		s,
		c,
		l
	];
}
function em(e, t, n) {
	if (t = +t, e = +e, n = +n, !(n > 0)) return [];
	if (e === t) return [e];
	let r = t < e, [i, a, o] = r ? $p(t, e, n) : $p(e, t, n);
	if (!(a >= i)) return [];
	let s = a - i + 1, c = Array(s);
	if (r) if (o < 0) for (let e = 0; e < s; ++e) c[e] = (a - e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (a - e) * o;
	else if (o < 0) for (let e = 0; e < s; ++e) c[e] = (i + e) / -o;
	else for (let e = 0; e < s; ++e) c[e] = (i + e) * o;
	return c;
}
function tm(e, t, n) {
	return t = +t, e = +e, n = +n, $p(e, t, n)[2];
}
function nm(e, t, n) {
	t = +t, e = +e, n = +n;
	let r = t < e, i = r ? tm(t, e, n) : tm(e, t, n);
	return (r ? -1 : 1) * (i < 0 ? 1 / -i : i);
}
//#endregion
//#region node_modules/d3-array/src/max.js
function rm(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n < t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n < i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/min.js
function im(e, t) {
	let n;
	if (t === void 0) for (let t of e) t != null && (n > t || n === void 0 && t >= t) && (n = t);
	else {
		let r = -1;
		for (let i of e) (i = t(i, ++r, e)) != null && (n > i || n === void 0 && i >= i) && (n = i);
	}
	return n;
}
//#endregion
//#region node_modules/d3-array/src/quickselect.js
function am(e, t, n = 0, r = Infinity, i) {
	if (t = Math.floor(t), n = Math.floor(Math.max(0, n)), r = Math.floor(Math.min(e.length - 1, r)), !(n <= t && t <= r)) return e;
	for (i = i === void 0 ? Yp : Jp(i); r > n;) {
		if (r - n > 600) {
			let a = r - n + 1, o = t - n + 1, s = Math.log(a), c = .5 * Math.exp(2 * s / 3), l = .5 * Math.sqrt(s * c * (a - c) / a) * (o - a / 2 < 0 ? -1 : 1), u = Math.max(n, Math.floor(t - o * c / a + l)), d = Math.min(r, Math.floor(t + (a - o) * c / a + l));
			am(e, t, u, d, i);
		}
		let a = e[t], o = n, s = r;
		for (om(e, n, t), i(e[r], a) > 0 && om(e, n, r); o < s;) {
			for (om(e, o, s), ++o, --s; i(e[o], a) < 0;) ++o;
			for (; i(e[s], a) > 0;) --s;
		}
		i(e[n], a) === 0 ? om(e, n, s) : (++s, om(e, s, r)), s <= t && (n = s + 1), t <= s && (r = s - 1);
	}
	return e;
}
function om(e, t, n) {
	let r = e[t];
	e[t] = e[n], e[n] = r;
}
//#endregion
//#region node_modules/d3-array/src/quantile.js
function sm(e, t, n) {
	if (e = Float64Array.from(Bp(e, n)), !(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return im(e);
		if (t >= 1) return rm(e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = rm(am(e, a).subarray(0, a + 1));
		return o + (im(e.subarray(a + 1)) - o) * (i - a);
	}
}
function cm(e, t, n = zp) {
	if (!(!(r = e.length) || isNaN(t = +t))) {
		if (t <= 0 || r < 2) return +n(e[0], 0, e);
		if (t >= 1) return +n(e[r - 1], r - 1, e);
		var r, i = (r - 1) * t, a = Math.floor(i), o = +n(e[a], a, e);
		return o + (+n(e[a + 1], a + 1, e) - o) * (i - a);
	}
}
//#endregion
//#region node_modules/d3-array/src/range.js
function lm(e, t, n) {
	e = +e, t = +t, n = (i = arguments.length) < 2 ? (t = e, e = 0, 1) : i < 3 ? 1 : +n;
	for (var r = -1, i = Math.max(0, Math.ceil((t - e) / n)) | 0, a = Array(i); ++r < i;) a[r] = e + r * n;
	return a;
}
//#endregion
//#region node_modules/d3-scale/src/init.js
function um(e, t) {
	switch (arguments.length) {
		case 0: break;
		case 1:
			this.range(e);
			break;
		default:
			this.range(t).domain(e);
			break;
	}
	return this;
}
function dm(e, t) {
	switch (arguments.length) {
		case 0: break;
		case 1:
			typeof e == "function" ? this.interpolator(e) : this.range(e);
			break;
		default:
			this.domain(e), typeof t == "function" ? this.interpolator(t) : this.range(t);
			break;
	}
	return this;
}
//#endregion
//#region node_modules/d3-scale/src/ordinal.js
var fm = Symbol("implicit");
function pm() {
	var e = new Up(), t = [], n = [], r = fm;
	function i(i) {
		let a = e.get(i);
		if (a === void 0) {
			if (r !== fm) return r;
			e.set(i, a = t.push(i) - 1);
		}
		return n[a % n.length];
	}
	return i.domain = function(n) {
		if (!arguments.length) return t.slice();
		t = [], e = new Up();
		for (let r of n) e.has(r) || e.set(r, t.push(r) - 1);
		return i;
	}, i.range = function(e) {
		return arguments.length ? (n = Array.from(e), i) : n.slice();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return pm(t, n).unknown(r);
	}, um.apply(i, arguments), i;
}
//#endregion
//#region node_modules/d3-scale/src/band.js
function mm() {
	var e = pm().unknown(void 0), t = e.domain, n = e.range, r = 0, i = 1, a, o, s = !1, c = 0, l = 0, u = .5;
	delete e.unknown;
	function d() {
		var e = t().length, d = i < r, f = d ? i : r, p = d ? r : i;
		a = (p - f) / Math.max(1, e - c + l * 2), s && (a = Math.floor(a)), f += (p - f - a * (e - c)) * u, o = a * (1 - c), s && (f = Math.round(f), o = Math.round(o));
		var m = lm(e).map(function(e) {
			return f + a * e;
		});
		return n(d ? m.reverse() : m);
	}
	return e.domain = function(e) {
		return arguments.length ? (t(e), d()) : t();
	}, e.range = function(e) {
		return arguments.length ? ([r, i] = e, r = +r, i = +i, d()) : [r, i];
	}, e.rangeRound = function(e) {
		return [r, i] = e, r = +r, i = +i, s = !0, d();
	}, e.bandwidth = function() {
		return o;
	}, e.step = function() {
		return a;
	}, e.round = function(e) {
		return arguments.length ? (s = !!e, d()) : s;
	}, e.padding = function(e) {
		return arguments.length ? (c = Math.min(1, l = +e), d()) : c;
	}, e.paddingInner = function(e) {
		return arguments.length ? (c = Math.min(1, e), d()) : c;
	}, e.paddingOuter = function(e) {
		return arguments.length ? (l = +e, d()) : l;
	}, e.align = function(e) {
		return arguments.length ? (u = Math.max(0, Math.min(1, e)), d()) : u;
	}, e.copy = function() {
		return mm(t(), [r, i]).round(s).paddingInner(c).paddingOuter(l).align(u);
	}, um.apply(d(), arguments);
}
function hm(e) {
	var t = e.copy;
	return e.padding = e.paddingOuter, delete e.paddingInner, delete e.paddingOuter, e.copy = function() {
		return hm(t());
	}, e;
}
function gm() {
	return hm(mm.apply(null, arguments).paddingInner(1));
}
//#endregion
//#region node_modules/d3-color/src/define.js
function _m(e, t, n) {
	e.prototype = t.prototype = n, n.constructor = e;
}
function vm(e, t) {
	var n = Object.create(e.prototype);
	for (var r in t) n[r] = t[r];
	return n;
}
//#endregion
//#region node_modules/d3-color/src/color.js
function ym() {}
var bm = .7, xm = 1 / bm, Sm = "\\s*([+-]?\\d+)\\s*", Cm = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)\\s*", wm = "\\s*([+-]?(?:\\d*\\.)?\\d+(?:[eE][+-]?\\d+)?)%\\s*", Tm = /^#([0-9a-f]{3,8})$/, Em = RegExp(`^rgb\\(${Sm},${Sm},${Sm}\\)$`), Dm = RegExp(`^rgb\\(${wm},${wm},${wm}\\)$`), Om = RegExp(`^rgba\\(${Sm},${Sm},${Sm},${Cm}\\)$`), km = RegExp(`^rgba\\(${wm},${wm},${wm},${Cm}\\)$`), Am = RegExp(`^hsl\\(${Cm},${wm},${wm}\\)$`), jm = RegExp(`^hsla\\(${Cm},${wm},${wm},${Cm}\\)$`), Mm = {
	aliceblue: 15792383,
	antiquewhite: 16444375,
	aqua: 65535,
	aquamarine: 8388564,
	azure: 15794175,
	beige: 16119260,
	bisque: 16770244,
	black: 0,
	blanchedalmond: 16772045,
	blue: 255,
	blueviolet: 9055202,
	brown: 10824234,
	burlywood: 14596231,
	cadetblue: 6266528,
	chartreuse: 8388352,
	chocolate: 13789470,
	coral: 16744272,
	cornflowerblue: 6591981,
	cornsilk: 16775388,
	crimson: 14423100,
	cyan: 65535,
	darkblue: 139,
	darkcyan: 35723,
	darkgoldenrod: 12092939,
	darkgray: 11119017,
	darkgreen: 25600,
	darkgrey: 11119017,
	darkkhaki: 12433259,
	darkmagenta: 9109643,
	darkolivegreen: 5597999,
	darkorange: 16747520,
	darkorchid: 10040012,
	darkred: 9109504,
	darksalmon: 15308410,
	darkseagreen: 9419919,
	darkslateblue: 4734347,
	darkslategray: 3100495,
	darkslategrey: 3100495,
	darkturquoise: 52945,
	darkviolet: 9699539,
	deeppink: 16716947,
	deepskyblue: 49151,
	dimgray: 6908265,
	dimgrey: 6908265,
	dodgerblue: 2003199,
	firebrick: 11674146,
	floralwhite: 16775920,
	forestgreen: 2263842,
	fuchsia: 16711935,
	gainsboro: 14474460,
	ghostwhite: 16316671,
	gold: 16766720,
	goldenrod: 14329120,
	gray: 8421504,
	green: 32768,
	greenyellow: 11403055,
	grey: 8421504,
	honeydew: 15794160,
	hotpink: 16738740,
	indianred: 13458524,
	indigo: 4915330,
	ivory: 16777200,
	khaki: 15787660,
	lavender: 15132410,
	lavenderblush: 16773365,
	lawngreen: 8190976,
	lemonchiffon: 16775885,
	lightblue: 11393254,
	lightcoral: 15761536,
	lightcyan: 14745599,
	lightgoldenrodyellow: 16448210,
	lightgray: 13882323,
	lightgreen: 9498256,
	lightgrey: 13882323,
	lightpink: 16758465,
	lightsalmon: 16752762,
	lightseagreen: 2142890,
	lightskyblue: 8900346,
	lightslategray: 7833753,
	lightslategrey: 7833753,
	lightsteelblue: 11584734,
	lightyellow: 16777184,
	lime: 65280,
	limegreen: 3329330,
	linen: 16445670,
	magenta: 16711935,
	maroon: 8388608,
	mediumaquamarine: 6737322,
	mediumblue: 205,
	mediumorchid: 12211667,
	mediumpurple: 9662683,
	mediumseagreen: 3978097,
	mediumslateblue: 8087790,
	mediumspringgreen: 64154,
	mediumturquoise: 4772300,
	mediumvioletred: 13047173,
	midnightblue: 1644912,
	mintcream: 16121850,
	mistyrose: 16770273,
	moccasin: 16770229,
	navajowhite: 16768685,
	navy: 128,
	oldlace: 16643558,
	olive: 8421376,
	olivedrab: 7048739,
	orange: 16753920,
	orangered: 16729344,
	orchid: 14315734,
	palegoldenrod: 15657130,
	palegreen: 10025880,
	paleturquoise: 11529966,
	palevioletred: 14381203,
	papayawhip: 16773077,
	peachpuff: 16767673,
	peru: 13468991,
	pink: 16761035,
	plum: 14524637,
	powderblue: 11591910,
	purple: 8388736,
	rebeccapurple: 6697881,
	red: 16711680,
	rosybrown: 12357519,
	royalblue: 4286945,
	saddlebrown: 9127187,
	salmon: 16416882,
	sandybrown: 16032864,
	seagreen: 3050327,
	seashell: 16774638,
	sienna: 10506797,
	silver: 12632256,
	skyblue: 8900331,
	slateblue: 6970061,
	slategray: 7372944,
	slategrey: 7372944,
	snow: 16775930,
	springgreen: 65407,
	steelblue: 4620980,
	tan: 13808780,
	teal: 32896,
	thistle: 14204888,
	tomato: 16737095,
	turquoise: 4251856,
	violet: 15631086,
	wheat: 16113331,
	white: 16777215,
	whitesmoke: 16119285,
	yellow: 16776960,
	yellowgreen: 10145074
};
_m(ym, Lm, {
	copy(e) {
		return Object.assign(new this.constructor(), this, e);
	},
	displayable() {
		return this.rgb().displayable();
	},
	hex: Nm,
	formatHex: Nm,
	formatHex8: Pm,
	formatHsl: Fm,
	formatRgb: Im,
	toString: Im
});
function Nm() {
	return this.rgb().formatHex();
}
function Pm() {
	return this.rgb().formatHex8();
}
function Fm() {
	return Xm(this).formatHsl();
}
function Im() {
	return this.rgb().formatRgb();
}
function Lm(e) {
	var t, n;
	return e = (e + "").trim().toLowerCase(), (t = Tm.exec(e)) ? (n = t[1].length, t = parseInt(t[1], 16), n === 6 ? Rm(t) : n === 3 ? new Hm(t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, (t & 15) << 4 | t & 15, 1) : n === 8 ? zm(t >> 24 & 255, t >> 16 & 255, t >> 8 & 255, (t & 255) / 255) : n === 4 ? zm(t >> 12 & 15 | t >> 8 & 240, t >> 8 & 15 | t >> 4 & 240, t >> 4 & 15 | t & 240, ((t & 15) << 4 | t & 15) / 255) : null) : (t = Em.exec(e)) ? new Hm(t[1], t[2], t[3], 1) : (t = Dm.exec(e)) ? new Hm(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, 1) : (t = Om.exec(e)) ? zm(t[1], t[2], t[3], t[4]) : (t = km.exec(e)) ? zm(t[1] * 255 / 100, t[2] * 255 / 100, t[3] * 255 / 100, t[4]) : (t = Am.exec(e)) ? Ym(t[1], t[2] / 100, t[3] / 100, 1) : (t = jm.exec(e)) ? Ym(t[1], t[2] / 100, t[3] / 100, t[4]) : Mm.hasOwnProperty(e) ? Rm(Mm[e]) : e === "transparent" ? new Hm(NaN, NaN, NaN, 0) : null;
}
function Rm(e) {
	return new Hm(e >> 16 & 255, e >> 8 & 255, e & 255, 1);
}
function zm(e, t, n, r) {
	return r <= 0 && (e = t = n = NaN), new Hm(e, t, n, r);
}
function Bm(e) {
	return e instanceof ym || (e = Lm(e)), e ? (e = e.rgb(), new Hm(e.r, e.g, e.b, e.opacity)) : new Hm();
}
function Vm(e, t, n, r) {
	return arguments.length === 1 ? Bm(e) : new Hm(e, t, n, r == null ? 1 : r);
}
function Hm(e, t, n, r) {
	this.r = +e, this.g = +t, this.b = +n, this.opacity = +r;
}
_m(Hm, Vm, vm(ym, {
	brighter(e) {
		return e = e == null ? xm : xm ** +e, new Hm(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? bm : bm ** +e, new Hm(this.r * e, this.g * e, this.b * e, this.opacity);
	},
	rgb() {
		return this;
	},
	clamp() {
		return new Hm(qm(this.r), qm(this.g), qm(this.b), Km(this.opacity));
	},
	displayable() {
		return -.5 <= this.r && this.r < 255.5 && -.5 <= this.g && this.g < 255.5 && -.5 <= this.b && this.b < 255.5 && 0 <= this.opacity && this.opacity <= 1;
	},
	hex: Um,
	formatHex: Um,
	formatHex8: Wm,
	formatRgb: Gm,
	toString: Gm
}));
function Um() {
	return `#${Jm(this.r)}${Jm(this.g)}${Jm(this.b)}`;
}
function Wm() {
	return `#${Jm(this.r)}${Jm(this.g)}${Jm(this.b)}${Jm((isNaN(this.opacity) ? 1 : this.opacity) * 255)}`;
}
function Gm() {
	let e = Km(this.opacity);
	return `${e === 1 ? "rgb(" : "rgba("}${qm(this.r)}, ${qm(this.g)}, ${qm(this.b)}${e === 1 ? ")" : `, ${e})`}`;
}
function Km(e) {
	return isNaN(e) ? 1 : Math.max(0, Math.min(1, e));
}
function qm(e) {
	return Math.max(0, Math.min(255, Math.round(e) || 0));
}
function Jm(e) {
	return e = qm(e), (e < 16 ? "0" : "") + e.toString(16);
}
function Ym(e, t, n, r) {
	return r <= 0 ? e = t = n = NaN : n <= 0 || n >= 1 ? e = t = NaN : t <= 0 && (e = NaN), new Qm(e, t, n, r);
}
function Xm(e) {
	if (e instanceof Qm) return new Qm(e.h, e.s, e.l, e.opacity);
	if (e instanceof ym || (e = Lm(e)), !e) return new Qm();
	if (e instanceof Qm) return e;
	e = e.rgb();
	var t = e.r / 255, n = e.g / 255, r = e.b / 255, i = Math.min(t, n, r), a = Math.max(t, n, r), o = NaN, s = a - i, c = (a + i) / 2;
	return s ? (o = t === a ? (n - r) / s + (n < r) * 6 : n === a ? (r - t) / s + 2 : (t - n) / s + 4, s /= c < .5 ? a + i : 2 - a - i, o *= 60) : s = c > 0 && c < 1 ? 0 : o, new Qm(o, s, c, e.opacity);
}
function Zm(e, t, n, r) {
	return arguments.length === 1 ? Xm(e) : new Qm(e, t, n, r == null ? 1 : r);
}
function Qm(e, t, n, r) {
	this.h = +e, this.s = +t, this.l = +n, this.opacity = +r;
}
_m(Qm, Zm, vm(ym, {
	brighter(e) {
		return e = e == null ? xm : xm ** +e, new Qm(this.h, this.s, this.l * e, this.opacity);
	},
	darker(e) {
		return e = e == null ? bm : bm ** +e, new Qm(this.h, this.s, this.l * e, this.opacity);
	},
	rgb() {
		var e = this.h % 360 + (this.h < 0) * 360, t = isNaN(e) || isNaN(this.s) ? 0 : this.s, n = this.l, r = n + (n < .5 ? n : 1 - n) * t, i = 2 * n - r;
		return new Hm(th(e >= 240 ? e - 240 : e + 120, i, r), th(e, i, r), th(e < 120 ? e + 240 : e - 120, i, r), this.opacity);
	},
	clamp() {
		return new Qm($m(this.h), eh(this.s), eh(this.l), Km(this.opacity));
	},
	displayable() {
		return (0 <= this.s && this.s <= 1 || isNaN(this.s)) && 0 <= this.l && this.l <= 1 && 0 <= this.opacity && this.opacity <= 1;
	},
	formatHsl() {
		let e = Km(this.opacity);
		return `${e === 1 ? "hsl(" : "hsla("}${$m(this.h)}, ${eh(this.s) * 100}%, ${eh(this.l) * 100}%${e === 1 ? ")" : `, ${e})`}`;
	}
}));
function $m(e) {
	return e = (e || 0) % 360, e < 0 ? e + 360 : e;
}
function eh(e) {
	return Math.max(0, Math.min(1, e || 0));
}
function th(e, t, n) {
	return (e < 60 ? t + (n - t) * e / 60 : e < 180 ? n : e < 240 ? t + (n - t) * (240 - e) / 60 : t) * 255;
}
//#endregion
//#region node_modules/d3-interpolate/src/constant.js
var nh = (e) => () => e;
//#endregion
//#region node_modules/d3-interpolate/src/color.js
function rh(e, t) {
	return function(n) {
		return e + n * t;
	};
}
function ih(e, t, n) {
	return e **= +n, t = t ** +n - e, n = 1 / n, function(r) {
		return (e + r * t) ** +n;
	};
}
function ah(e) {
	return (e = +e) == 1 ? oh : function(t, n) {
		return n - t ? ih(t, n, e) : nh(isNaN(t) ? n : t);
	};
}
function oh(e, t) {
	var n = t - e;
	return n ? rh(e, n) : nh(isNaN(e) ? t : e);
}
//#endregion
//#region node_modules/d3-interpolate/src/rgb.js
var sh = (function e(t) {
	var n = ah(t);
	function r(e, t) {
		var r = n((e = Vm(e)).r, (t = Vm(t)).r), i = n(e.g, t.g), a = n(e.b, t.b), o = oh(e.opacity, t.opacity);
		return function(t) {
			return e.r = r(t), e.g = i(t), e.b = a(t), e.opacity = o(t), e + "";
		};
	}
	return r.gamma = e, r;
})(1);
//#endregion
//#region node_modules/d3-interpolate/src/numberArray.js
function ch(e, t) {
	t || (t = []);
	var n = e ? Math.min(t.length, e.length) : 0, r = t.slice(), i;
	return function(a) {
		for (i = 0; i < n; ++i) r[i] = e[i] * (1 - a) + t[i] * a;
		return r;
	};
}
function lh(e) {
	return ArrayBuffer.isView(e) && !(e instanceof DataView);
}
//#endregion
//#region node_modules/d3-interpolate/src/array.js
function uh(e, t) {
	var n = t ? t.length : 0, r = e ? Math.min(n, e.length) : 0, i = Array(r), a = Array(n), o;
	for (o = 0; o < r; ++o) i[o] = yh(e[o], t[o]);
	for (; o < n; ++o) a[o] = t[o];
	return function(e) {
		for (o = 0; o < r; ++o) a[o] = i[o](e);
		return a;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/date.js
function dh(e, t) {
	var n = /* @__PURE__ */ new Date();
	return e = +e, t = +t, function(r) {
		return n.setTime(e * (1 - r) + t * r), n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/number.js
function fh(e, t) {
	return e = +e, t = +t, function(n) {
		return e * (1 - n) + t * n;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/object.js
function ph(e, t) {
	var n = {}, r = {}, i;
	for (i in (typeof e != "object" || !e) && (e = {}), (typeof t != "object" || !t) && (t = {}), t) i in e ? n[i] = yh(e[i], t[i]) : r[i] = t[i];
	return function(e) {
		for (i in n) r[i] = n[i](e);
		return r;
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/string.js
var mh = /[-+]?(?:\d+\.?\d*|\.?\d+)(?:[eE][-+]?\d+)?/g, hh = new RegExp(mh.source, "g");
function gh(e) {
	return function() {
		return e;
	};
}
function _h(e) {
	return function(t) {
		return e(t) + "";
	};
}
function vh(e, t) {
	var n = mh.lastIndex = hh.lastIndex = 0, r, i, a, o = -1, s = [], c = [];
	for (e += "", t += ""; (r = mh.exec(e)) && (i = hh.exec(t));) (a = i.index) > n && (a = t.slice(n, a), s[o] ? s[o] += a : s[++o] = a), (r = r[0]) === (i = i[0]) ? s[o] ? s[o] += i : s[++o] = i : (s[++o] = null, c.push({
		i: o,
		x: fh(r, i)
	})), n = hh.lastIndex;
	return n < t.length && (a = t.slice(n), s[o] ? s[o] += a : s[++o] = a), s.length < 2 ? c[0] ? _h(c[0].x) : gh(t) : (t = c.length, function(e) {
		for (var n = 0, r; n < t; ++n) s[(r = c[n]).i] = r.x(e);
		return s.join("");
	});
}
//#endregion
//#region node_modules/d3-interpolate/src/value.js
function yh(e, t) {
	var n = typeof t, r;
	return t == null || n === "boolean" ? nh(t) : (n === "number" ? fh : n === "string" ? (r = Lm(t)) ? (t = r, sh) : vh : t instanceof Lm ? sh : t instanceof Date ? dh : lh(t) ? ch : Array.isArray(t) ? uh : typeof t.valueOf != "function" && typeof t.toString != "function" || isNaN(t) ? ph : fh)(e, t);
}
//#endregion
//#region node_modules/d3-interpolate/src/round.js
function bh(e, t) {
	return e = +e, t = +t, function(n) {
		return Math.round(e * (1 - n) + t * n);
	};
}
//#endregion
//#region node_modules/d3-interpolate/src/piecewise.js
function xh(e, t) {
	t === void 0 && (t = e, e = yh);
	for (var n = 0, r = t.length - 1, i = t[0], a = Array(r < 0 ? 0 : r); n < r;) a[n] = e(i, i = t[++n]);
	return function(e) {
		var t = Math.max(0, Math.min(r - 1, Math.floor(e *= r)));
		return a[t](e - t);
	};
}
//#endregion
//#region node_modules/d3-scale/src/constant.js
function Sh(e) {
	return function() {
		return e;
	};
}
//#endregion
//#region node_modules/d3-scale/src/number.js
function Ch(e) {
	return +e;
}
//#endregion
//#region node_modules/d3-scale/src/continuous.js
var wh = [0, 1];
function Th(e) {
	return e;
}
function Eh(e, t) {
	return (t -= e = +e) ? function(n) {
		return (n - e) / t;
	} : Sh(isNaN(t) ? NaN : .5);
}
function Dh(e, t) {
	var n;
	return e > t && (n = e, e = t, t = n), function(n) {
		return Math.max(e, Math.min(t, n));
	};
}
function Oh(e, t, n) {
	var r = e[0], i = e[1], a = t[0], o = t[1];
	return i < r ? (r = Eh(i, r), a = n(o, a)) : (r = Eh(r, i), a = n(a, o)), function(e) {
		return a(r(e));
	};
}
function kh(e, t, n) {
	var r = Math.min(e.length, t.length) - 1, i = Array(r), a = Array(r), o = -1;
	for (e[r] < e[0] && (e = e.slice().reverse(), t = t.slice().reverse()); ++o < r;) i[o] = Eh(e[o], e[o + 1]), a[o] = n(t[o], t[o + 1]);
	return function(t) {
		var n = Hp(e, t, 1, r) - 1;
		return a[n](i[n](t));
	};
}
function Ah(e, t) {
	return t.domain(e.domain()).range(e.range()).interpolate(e.interpolate()).clamp(e.clamp()).unknown(e.unknown());
}
function jh() {
	var e = wh, t = wh, n = yh, r, i, a, o = Th, s, c, l;
	function u() {
		var n = Math.min(e.length, t.length);
		return o !== Th && (o = Dh(e[0], e[n - 1])), s = n > 2 ? kh : Oh, c = l = null, d;
	}
	function d(i) {
		return i == null || isNaN(i = +i) ? a : (c || (c = s(e.map(r), t, n)))(r(o(i)));
	}
	return d.invert = function(n) {
		return o(i((l || (l = s(t, e.map(r), fh)))(n)));
	}, d.domain = function(t) {
		return arguments.length ? (e = Array.from(t, Ch), u()) : e.slice();
	}, d.range = function(e) {
		return arguments.length ? (t = Array.from(e), u()) : t.slice();
	}, d.rangeRound = function(e) {
		return t = Array.from(e), n = bh, u();
	}, d.clamp = function(e) {
		return arguments.length ? (o = e ? !0 : Th, u()) : o !== Th;
	}, d.interpolate = function(e) {
		return arguments.length ? (n = e, u()) : n;
	}, d.unknown = function(e) {
		return arguments.length ? (a = e, d) : a;
	}, function(e, t) {
		return r = e, i = t, u();
	};
}
function Mh() {
	return jh()(Th, Th);
}
//#endregion
//#region node_modules/d3-format/src/formatDecimal.js
function Nh(e) {
	return Math.abs(e = Math.round(e)) >= 1e21 ? e.toLocaleString("en").replace(/,/g, "") : e.toString(10);
}
function Ph(e, t) {
	if (!isFinite(e) || e === 0) return null;
	var n = (e = t ? e.toExponential(t - 1) : e.toExponential()).indexOf("e"), r = e.slice(0, n);
	return [r.length > 1 ? r[0] + r.slice(2) : r, +e.slice(n + 1)];
}
//#endregion
//#region node_modules/d3-format/src/exponent.js
function Fh(e) {
	return e = Ph(Math.abs(e)), e ? e[1] : NaN;
}
//#endregion
//#region node_modules/d3-format/src/formatGroup.js
function Ih(e, t) {
	return function(n, r) {
		for (var i = n.length, a = [], o = 0, s = e[0], c = 0; i > 0 && s > 0 && (c + s + 1 > r && (s = Math.max(1, r - c)), a.push(n.substring(i -= s, i + s)), !((c += s + 1) > r));) s = e[o = (o + 1) % e.length];
		return a.reverse().join(t);
	};
}
//#endregion
//#region node_modules/d3-format/src/formatNumerals.js
function Lh(e) {
	return function(t) {
		return t.replace(/[0-9]/g, function(t) {
			return e[+t];
		});
	};
}
//#endregion
//#region node_modules/d3-format/src/formatSpecifier.js
var Rh = /^(?:(.)?([<>=^]))?([+\-( ])?([$#])?(0)?(\d+)?(,)?(\.\d+)?(~)?([a-z%])?$/i;
function zh(e) {
	if (!(t = Rh.exec(e))) throw Error("invalid format: " + e);
	var t;
	return new Bh({
		fill: t[1],
		align: t[2],
		sign: t[3],
		symbol: t[4],
		zero: t[5],
		width: t[6],
		comma: t[7],
		precision: t[8] && t[8].slice(1),
		trim: t[9],
		type: t[10]
	});
}
zh.prototype = Bh.prototype;
function Bh(e) {
	this.fill = e.fill === void 0 ? " " : e.fill + "", this.align = e.align === void 0 ? ">" : e.align + "", this.sign = e.sign === void 0 ? "-" : e.sign + "", this.symbol = e.symbol === void 0 ? "" : e.symbol + "", this.zero = !!e.zero, this.width = e.width === void 0 ? void 0 : +e.width, this.comma = !!e.comma, this.precision = e.precision === void 0 ? void 0 : +e.precision, this.trim = !!e.trim, this.type = e.type === void 0 ? "" : e.type + "";
}
Bh.prototype.toString = function() {
	return this.fill + this.align + this.sign + this.symbol + (this.zero ? "0" : "") + (this.width === void 0 ? "" : Math.max(1, this.width | 0)) + (this.comma ? "," : "") + (this.precision === void 0 ? "" : "." + Math.max(0, this.precision | 0)) + (this.trim ? "~" : "") + this.type;
};
//#endregion
//#region node_modules/d3-format/src/formatTrim.js
function Vh(e) {
	out: for (var t = e.length, n = 1, r = -1, i; n < t; ++n) switch (e[n]) {
		case ".":
			r = i = n;
			break;
		case "0":
			r === 0 && (r = n), i = n;
			break;
		default:
			if (!+e[n]) break out;
			r > 0 && (r = 0);
			break;
	}
	return r > 0 ? e.slice(0, r) + e.slice(i + 1) : e;
}
//#endregion
//#region node_modules/d3-format/src/formatPrefixAuto.js
var Hh;
function Uh(e, t) {
	var n = Ph(e, t);
	if (!n) return Hh = void 0, e.toPrecision(t);
	var r = n[0], i = n[1], a = i - (Hh = Math.max(-8, Math.min(8, Math.floor(i / 3))) * 3) + 1, o = r.length;
	return a === o ? r : a > o ? r + Array(a - o + 1).join("0") : a > 0 ? r.slice(0, a) + "." + r.slice(a) : "0." + Array(1 - a).join("0") + Ph(e, Math.max(0, t + a - 1))[0];
}
//#endregion
//#region node_modules/d3-format/src/formatRounded.js
function Wh(e, t) {
	var n = Ph(e, t);
	if (!n) return e + "";
	var r = n[0], i = n[1];
	return i < 0 ? "0." + Array(-i).join("0") + r : r.length > i + 1 ? r.slice(0, i + 1) + "." + r.slice(i + 1) : r + Array(i - r.length + 2).join("0");
}
//#endregion
//#region node_modules/d3-format/src/formatTypes.js
var Gh = {
	"%": (e, t) => (e * 100).toFixed(t),
	b: (e) => Math.round(e).toString(2),
	c: (e) => e + "",
	d: Nh,
	e: (e, t) => e.toExponential(t),
	f: (e, t) => e.toFixed(t),
	g: (e, t) => e.toPrecision(t),
	o: (e) => Math.round(e).toString(8),
	p: (e, t) => Wh(e * 100, t),
	r: Wh,
	s: Uh,
	X: (e) => Math.round(e).toString(16).toUpperCase(),
	x: (e) => Math.round(e).toString(16)
};
//#endregion
//#region node_modules/d3-format/src/identity.js
function Kh(e) {
	return e;
}
//#endregion
//#region node_modules/d3-format/src/locale.js
var qh = Array.prototype.map, Jh = [
	"y",
	"z",
	"a",
	"f",
	"p",
	"n",
	"µ",
	"m",
	"",
	"k",
	"M",
	"G",
	"T",
	"P",
	"E",
	"Z",
	"Y"
];
function Yh(e) {
	var t = e.grouping === void 0 || e.thousands === void 0 ? Kh : Ih(qh.call(e.grouping, Number), e.thousands + ""), n = e.currency === void 0 ? "" : e.currency[0] + "", r = e.currency === void 0 ? "" : e.currency[1] + "", i = e.decimal === void 0 ? "." : e.decimal + "", a = e.numerals === void 0 ? Kh : Lh(qh.call(e.numerals, String)), o = e.percent === void 0 ? "%" : e.percent + "", s = e.minus === void 0 ? "−" : e.minus + "", c = e.nan === void 0 ? "NaN" : e.nan + "";
	function l(e, l) {
		e = zh(e);
		var u = e.fill, d = e.align, f = e.sign, p = e.symbol, m = e.zero, h = e.width, g = e.comma, _ = e.precision, v = e.trim, y = e.type;
		y === "n" ? (g = !0, y = "g") : Gh[y] || (_ === void 0 && (_ = 12), v = !0, y = "g"), (m || u === "0" && d === "=") && (m = !0, u = "0", d = "=");
		var b = (l && l.prefix !== void 0 ? l.prefix : "") + (p === "$" ? n : p === "#" && /[boxX]/.test(y) ? "0" + y.toLowerCase() : ""), x = (p === "$" ? r : /[%p]/.test(y) ? o : "") + (l && l.suffix !== void 0 ? l.suffix : ""), S = Gh[y], C = /[defgprs%]/.test(y);
		_ = _ === void 0 ? 6 : /[gprs]/.test(y) ? Math.max(1, Math.min(21, _)) : Math.max(0, Math.min(20, _));
		function w(e) {
			var n = b, r = x, o, l, p;
			if (y === "c") r = S(e) + r, e = "";
			else {
				e = +e;
				var w = e < 0 || 1 / e < 0;
				if (e = isNaN(e) ? c : S(Math.abs(e), _), v && (e = Vh(e)), w && +e == 0 && f !== "+" && (w = !1), n = (w ? f === "(" ? f : s : f === "-" || f === "(" ? "" : f) + n, r = (y === "s" && !isNaN(e) && Hh !== void 0 ? Jh[8 + Hh / 3] : "") + r + (w && f === "(" ? ")" : ""), C) {
					for (o = -1, l = e.length; ++o < l;) if (p = e.charCodeAt(o), 48 > p || p > 57) {
						r = (p === 46 ? i + e.slice(o + 1) : e.slice(o)) + r, e = e.slice(0, o);
						break;
					}
				}
			}
			g && !m && (e = t(e, Infinity));
			var T = n.length + e.length + r.length, E = T < h ? Array(h - T + 1).join(u) : "";
			switch (g && m && (e = t(E + e, E.length ? h - r.length : Infinity), E = ""), d) {
				case "<":
					e = n + e + r + E;
					break;
				case "=":
					e = n + E + e + r;
					break;
				case "^":
					e = E.slice(0, T = E.length >> 1) + n + e + r + E.slice(T);
					break;
				default:
					e = E + n + e + r;
					break;
			}
			return a(e);
		}
		return w.toString = function() {
			return e + "";
		}, w;
	}
	function u(e, t) {
		var n = Math.max(-8, Math.min(8, Math.floor(Fh(t) / 3))) * 3, r = 10 ** -n, i = l((e = zh(e), e.type = "f", e), { suffix: Jh[8 + n / 3] });
		return function(e) {
			return i(r * e);
		};
	}
	return {
		format: l,
		formatPrefix: u
	};
}
//#endregion
//#region node_modules/d3-format/src/defaultLocale.js
var Xh, Zh, Qh;
$h({
	thousands: ",",
	grouping: [3],
	currency: ["$", ""]
});
function $h(e) {
	return Xh = Yh(e), Zh = Xh.format, Qh = Xh.formatPrefix, Xh;
}
//#endregion
//#region node_modules/d3-format/src/precisionFixed.js
function eg(e) {
	return Math.max(0, -Fh(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionPrefix.js
function tg(e, t) {
	return Math.max(0, Math.max(-8, Math.min(8, Math.floor(Fh(t) / 3))) * 3 - Fh(Math.abs(e)));
}
//#endregion
//#region node_modules/d3-format/src/precisionRound.js
function ng(e, t) {
	return e = Math.abs(e), t = Math.abs(t) - e, Math.max(0, Fh(t) - Fh(e)) + 1;
}
//#endregion
//#region node_modules/d3-scale/src/tickFormat.js
function rg(e, t, n, r) {
	var i = nm(e, t, n), a;
	switch (r = zh(r == null ? ",f" : r), r.type) {
		case "s":
			var o = Math.max(Math.abs(e), Math.abs(t));
			return r.precision == null && !isNaN(a = tg(i, o)) && (r.precision = a), Qh(r, o);
		case "":
		case "e":
		case "g":
		case "p":
		case "r":
			r.precision == null && !isNaN(a = ng(i, Math.max(Math.abs(e), Math.abs(t)))) && (r.precision = a - (r.type === "e"));
			break;
		case "f":
		case "%":
			r.precision == null && !isNaN(a = eg(i)) && (r.precision = a - (r.type === "%") * 2);
			break;
	}
	return Zh(r);
}
//#endregion
//#region node_modules/d3-scale/src/linear.js
function ig(e) {
	var t = e.domain;
	return e.ticks = function(e) {
		var n = t();
		return em(n[0], n[n.length - 1], e == null ? 10 : e);
	}, e.tickFormat = function(e, n) {
		var r = t();
		return rg(r[0], r[r.length - 1], e == null ? 10 : e, n);
	}, e.nice = function(n) {
		n == null && (n = 10);
		var r = t(), i = 0, a = r.length - 1, o = r[i], s = r[a], c, l, u = 10;
		for (s < o && (l = o, o = s, s = l, l = i, i = a, a = l); u-- > 0;) {
			if (l = tm(o, s, n), l === c) return r[i] = o, r[a] = s, t(r);
			if (l > 0) o = Math.floor(o / l) * l, s = Math.ceil(s / l) * l;
			else if (l < 0) o = Math.ceil(o * l) / l, s = Math.floor(s * l) / l;
			else break;
			c = l;
		}
		return e;
	}, e;
}
function ag() {
	var e = Mh();
	return e.copy = function() {
		return Ah(e, ag());
	}, um.apply(e, arguments), ig(e);
}
//#endregion
//#region node_modules/d3-scale/src/identity.js
function og(e) {
	var t;
	function n(e) {
		return e == null || isNaN(e = +e) ? t : e;
	}
	return n.invert = n, n.domain = n.range = function(t) {
		return arguments.length ? (e = Array.from(t, Ch), n) : e.slice();
	}, n.unknown = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.copy = function() {
		return og(e).unknown(t);
	}, e = arguments.length ? Array.from(e, Ch) : [0, 1], ig(n);
}
//#endregion
//#region node_modules/d3-scale/src/nice.js
function sg(e, t) {
	e = e.slice();
	var n = 0, r = e.length - 1, i = e[n], a = e[r], o;
	return a < i && (o = n, n = r, r = o, o = i, i = a, a = o), e[n] = t.floor(i), e[r] = t.ceil(a), e;
}
//#endregion
//#region node_modules/d3-scale/src/log.js
function cg(e) {
	return Math.log(e);
}
function lg(e) {
	return Math.exp(e);
}
function ug(e) {
	return -Math.log(-e);
}
function dg(e) {
	return -Math.exp(-e);
}
function fg(e) {
	return isFinite(e) ? +("1e" + e) : e < 0 ? 0 : e;
}
function pg(e) {
	return e === 10 ? fg : e === Math.E ? Math.exp : (t) => e ** +t;
}
function mg(e) {
	return e === Math.E ? Math.log : e === 10 && Math.log10 || e === 2 && Math.log2 || (e = Math.log(e), (t) => Math.log(t) / e);
}
function hg(e) {
	return (t, n) => -e(-t, n);
}
function gg(e) {
	let t = e(cg, lg), n = t.domain, r = 10, i, a;
	function o() {
		return i = mg(r), a = pg(r), n()[0] < 0 ? (i = hg(i), a = hg(a), e(ug, dg)) : e(cg, lg), t;
	}
	return t.base = function(e) {
		return arguments.length ? (r = +e, o()) : r;
	}, t.domain = function(e) {
		return arguments.length ? (n(e), o()) : n();
	}, t.ticks = (e) => {
		let t = n(), o = t[0], s = t[t.length - 1], c = s < o;
		c && ([o, s] = [s, o]);
		let l = i(o), u = i(s), d, f, p = e == null ? 10 : +e, m = [];
		if (!(r % 1) && u - l < p) {
			if (l = Math.floor(l), u = Math.ceil(u), o > 0) {
				for (; l <= u; ++l) for (d = 1; d < r; ++d) if (f = l < 0 ? d / a(-l) : d * a(l), !(f < o)) {
					if (f > s) break;
					m.push(f);
				}
			} else for (; l <= u; ++l) for (d = r - 1; d >= 1; --d) if (f = l > 0 ? d / a(-l) : d * a(l), !(f < o)) {
				if (f > s) break;
				m.push(f);
			}
			m.length * 2 < p && (m = em(o, s, p));
		} else m = em(l, u, Math.min(u - l, p)).map(a);
		return c ? m.reverse() : m;
	}, t.tickFormat = (e, n) => {
		if (e == null && (e = 10), n == null && (n = r === 10 ? "s" : ","), typeof n != "function" && (!(r % 1) && (n = zh(n)).precision == null && (n.trim = !0), n = Zh(n)), e === Infinity) return n;
		let o = Math.max(1, r * e / t.ticks().length);
		return (e) => {
			let t = e / a(Math.round(i(e)));
			return t * r < r - .5 && (t *= r), t <= o ? n(e) : "";
		};
	}, t.nice = () => n(sg(n(), {
		floor: (e) => a(Math.floor(i(e))),
		ceil: (e) => a(Math.ceil(i(e)))
	})), t;
}
function _g() {
	let e = gg(jh()).domain([1, 10]);
	return e.copy = () => Ah(e, _g()).base(e.base()), um.apply(e, arguments), e;
}
//#endregion
//#region node_modules/d3-scale/src/symlog.js
function vg(e) {
	return function(t) {
		return Math.sign(t) * Math.log1p(Math.abs(t / e));
	};
}
function yg(e) {
	return function(t) {
		return Math.sign(t) * Math.expm1(Math.abs(t)) * e;
	};
}
function bg(e) {
	var t = 1, n = e(vg(t), yg(t));
	return n.constant = function(n) {
		return arguments.length ? e(vg(t = +n), yg(t)) : t;
	}, ig(n);
}
function xg() {
	var e = bg(jh());
	return e.copy = function() {
		return Ah(e, xg()).constant(e.constant());
	}, um.apply(e, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/pow.js
function Sg(e) {
	return function(t) {
		return t < 0 ? -((-t) ** +e) : t ** +e;
	};
}
function Cg(e) {
	return e < 0 ? -Math.sqrt(-e) : Math.sqrt(e);
}
function wg(e) {
	return e < 0 ? -e * e : e * e;
}
function Tg(e) {
	var t = e(Th, Th), n = 1;
	function r() {
		return n === 1 ? e(Th, Th) : n === .5 ? e(Cg, wg) : e(Sg(n), Sg(1 / n));
	}
	return t.exponent = function(e) {
		return arguments.length ? (n = +e, r()) : n;
	}, ig(t);
}
function Eg() {
	var e = Tg(jh());
	return e.copy = function() {
		return Ah(e, Eg()).exponent(e.exponent());
	}, um.apply(e, arguments), e;
}
function Dg() {
	return Eg.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/radial.js
function Og(e) {
	return Math.sign(e) * e * e;
}
function kg(e) {
	return Math.sign(e) * Math.sqrt(Math.abs(e));
}
function Ag() {
	var e = Mh(), t = [0, 1], n = !1, r;
	function i(t) {
		var i = kg(e(t));
		return isNaN(i) ? r : n ? Math.round(i) : i;
	}
	return i.invert = function(t) {
		return e.invert(Og(t));
	}, i.domain = function(t) {
		return arguments.length ? (e.domain(t), i) : e.domain();
	}, i.range = function(n) {
		return arguments.length ? (e.range((t = Array.from(n, Ch)).map(Og)), i) : t.slice();
	}, i.rangeRound = function(e) {
		return i.range(e).round(!0);
	}, i.round = function(e) {
		return arguments.length ? (n = !!e, i) : n;
	}, i.clamp = function(t) {
		return arguments.length ? (e.clamp(t), i) : e.clamp();
	}, i.unknown = function(e) {
		return arguments.length ? (r = e, i) : r;
	}, i.copy = function() {
		return Ag(e.domain(), t).round(n).clamp(e.clamp()).unknown(r);
	}, um.apply(i, arguments), ig(i);
}
//#endregion
//#region node_modules/d3-scale/src/quantile.js
function jg() {
	var e = [], t = [], n = [], r;
	function i() {
		var r = 0, i = Math.max(1, t.length);
		for (n = Array(i - 1); ++r < i;) n[r - 1] = cm(e, r / i);
		return a;
	}
	function a(e) {
		return e == null || isNaN(e = +e) ? r : t[Hp(n, e)];
	}
	return a.invertExtent = function(r) {
		var i = t.indexOf(r);
		return i < 0 ? [NaN, NaN] : [i > 0 ? n[i - 1] : e[0], i < n.length ? n[i] : e[e.length - 1]];
	}, a.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(Fp), i();
	}, a.range = function(e) {
		return arguments.length ? (t = Array.from(e), i()) : t.slice();
	}, a.unknown = function(e) {
		return arguments.length ? (r = e, a) : r;
	}, a.quantiles = function() {
		return n.slice();
	}, a.copy = function() {
		return jg().domain(e).range(t).unknown(r);
	}, um.apply(a, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/quantize.js
function Mg() {
	var e = 0, t = 1, n = 1, r = [.5], i = [0, 1], a;
	function o(e) {
		return e != null && e <= e ? i[Hp(r, e, 0, n)] : a;
	}
	function s() {
		var i = -1;
		for (r = Array(n); ++i < n;) r[i] = ((i + 1) * t - (i - n) * e) / (n + 1);
		return o;
	}
	return o.domain = function(n) {
		return arguments.length ? ([e, t] = n, e = +e, t = +t, s()) : [e, t];
	}, o.range = function(e) {
		return arguments.length ? (n = (i = Array.from(e)).length - 1, s()) : i.slice();
	}, o.invertExtent = function(a) {
		var o = i.indexOf(a);
		return o < 0 ? [NaN, NaN] : o < 1 ? [e, r[0]] : o >= n ? [r[n - 1], t] : [r[o - 1], r[o]];
	}, o.unknown = function(e) {
		return arguments.length && (a = e), o;
	}, o.thresholds = function() {
		return r.slice();
	}, o.copy = function() {
		return Mg().domain([e, t]).range(i).unknown(a);
	}, um.apply(ig(o), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/threshold.js
function Ng() {
	var e = [.5], t = [0, 1], n, r = 1;
	function i(i) {
		return i != null && i <= i ? t[Hp(e, i, 0, r)] : n;
	}
	return i.domain = function(n) {
		return arguments.length ? (e = Array.from(n), r = Math.min(e.length, t.length - 1), i) : e.slice();
	}, i.range = function(n) {
		return arguments.length ? (t = Array.from(n), r = Math.min(e.length, t.length - 1), i) : t.slice();
	}, i.invertExtent = function(n) {
		var r = t.indexOf(n);
		return [e[r - 1], e[r]];
	}, i.unknown = function(e) {
		return arguments.length ? (n = e, i) : n;
	}, i.copy = function() {
		return Ng().domain(e).range(t).unknown(n);
	}, um.apply(i, arguments);
}
//#endregion
//#region node_modules/d3-time/src/interval.js
var Pg = /* @__PURE__ */ new Date(), Fg = /* @__PURE__ */ new Date();
function Ig(e, t, n, r) {
	function i(t) {
		return e(t = arguments.length === 0 ? /* @__PURE__ */ new Date() : /* @__PURE__ */ new Date(+t)), t;
	}
	return i.floor = (t) => (e(t = /* @__PURE__ */ new Date(+t)), t), i.ceil = (n) => (e(n = /* @__PURE__ */ new Date(n - 1)), t(n, 1), e(n), n), i.round = (e) => {
		let t = i(e), n = i.ceil(e);
		return e - t < n - e ? t : n;
	}, i.offset = (e, n) => (t(e = /* @__PURE__ */ new Date(+e), n == null ? 1 : Math.floor(n)), e), i.range = (n, r, a) => {
		let o = [];
		if (n = i.ceil(n), a = a == null ? 1 : Math.floor(a), !(n < r) || !(a > 0)) return o;
		let s;
		do
			o.push(s = /* @__PURE__ */ new Date(+n)), t(n, a), e(n);
		while (s < n && n < r);
		return o;
	}, i.filter = (n) => Ig((t) => {
		if (t >= t) for (; e(t), !n(t);) t.setTime(t - 1);
	}, (e, r) => {
		if (e >= e) if (r < 0) for (; ++r <= 0;) for (; t(e, -1), !n(e););
		else for (; --r >= 0;) for (; t(e, 1), !n(e););
	}), n && (i.count = (t, r) => (Pg.setTime(+t), Fg.setTime(+r), e(Pg), e(Fg), Math.floor(n(Pg, Fg))), i.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? i.filter(r ? (t) => r(t) % e === 0 : (t) => i.count(0, t) % e === 0) : i)), i;
}
//#endregion
//#region node_modules/d3-time/src/millisecond.js
var Lg = Ig(() => {}, (e, t) => {
	e.setTime(+e + t);
}, (e, t) => t - e);
Lg.every = (e) => (e = Math.floor(e), !isFinite(e) || !(e > 0) ? null : e > 1 ? Ig((t) => {
	t.setTime(Math.floor(t / e) * e);
}, (t, n) => {
	t.setTime(+t + n * e);
}, (t, n) => (n - t) / e) : Lg), Lg.range;
//#endregion
//#region node_modules/d3-time/src/duration.js
var Rg = 1e3, zg = Rg * 60, Bg = zg * 60, Vg = Bg * 24, Hg = Vg * 7, Ug = Vg * 30, Wg = Vg * 365, Gg = Ig((e) => {
	e.setTime(e - e.getMilliseconds());
}, (e, t) => {
	e.setTime(+e + t * Rg);
}, (e, t) => (t - e) / Rg, (e) => e.getUTCSeconds());
Gg.range;
//#endregion
//#region node_modules/d3-time/src/minute.js
var Kg = Ig((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * Rg);
}, (e, t) => {
	e.setTime(+e + t * zg);
}, (e, t) => (t - e) / zg, (e) => e.getMinutes());
Kg.range;
var qg = Ig((e) => {
	e.setUTCSeconds(0, 0);
}, (e, t) => {
	e.setTime(+e + t * zg);
}, (e, t) => (t - e) / zg, (e) => e.getUTCMinutes());
qg.range;
//#endregion
//#region node_modules/d3-time/src/hour.js
var Jg = Ig((e) => {
	e.setTime(e - e.getMilliseconds() - e.getSeconds() * Rg - e.getMinutes() * zg);
}, (e, t) => {
	e.setTime(+e + t * Bg);
}, (e, t) => (t - e) / Bg, (e) => e.getHours());
Jg.range;
var Yg = Ig((e) => {
	e.setUTCMinutes(0, 0, 0);
}, (e, t) => {
	e.setTime(+e + t * Bg);
}, (e, t) => (t - e) / Bg, (e) => e.getUTCHours());
Yg.range;
//#endregion
//#region node_modules/d3-time/src/day.js
var Xg = Ig((e) => e.setHours(0, 0, 0, 0), (e, t) => e.setDate(e.getDate() + t), (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * zg) / Vg, (e) => e.getDate() - 1);
Xg.range;
var Zg = Ig((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / Vg, (e) => e.getUTCDate() - 1);
Zg.range;
var Qg = Ig((e) => {
	e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCDate(e.getUTCDate() + t);
}, (e, t) => (t - e) / Vg, (e) => Math.floor(e / Vg));
Qg.range;
//#endregion
//#region node_modules/d3-time/src/week.js
function $g(e) {
	return Ig((t) => {
		t.setDate(t.getDate() - (t.getDay() + 7 - e) % 7), t.setHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setDate(e.getDate() + t * 7);
	}, (e, t) => (t - e - (t.getTimezoneOffset() - e.getTimezoneOffset()) * zg) / Hg);
}
var e_ = $g(0), t_ = $g(1), n_ = $g(2), r_ = $g(3), i_ = $g(4), a_ = $g(5), o_ = $g(6);
e_.range, t_.range, n_.range, r_.range, i_.range, a_.range, o_.range;
function s_(e) {
	return Ig((t) => {
		t.setUTCDate(t.getUTCDate() - (t.getUTCDay() + 7 - e) % 7), t.setUTCHours(0, 0, 0, 0);
	}, (e, t) => {
		e.setUTCDate(e.getUTCDate() + t * 7);
	}, (e, t) => (t - e) / Hg);
}
var c_ = s_(0), l_ = s_(1), u_ = s_(2), d_ = s_(3), f_ = s_(4), p_ = s_(5), m_ = s_(6);
c_.range, l_.range, u_.range, d_.range, f_.range, p_.range, m_.range;
//#endregion
//#region node_modules/d3-time/src/month.js
var h_ = Ig((e) => {
	e.setDate(1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setMonth(e.getMonth() + t);
}, (e, t) => t.getMonth() - e.getMonth() + (t.getFullYear() - e.getFullYear()) * 12, (e) => e.getMonth());
h_.range;
var g_ = Ig((e) => {
	e.setUTCDate(1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCMonth(e.getUTCMonth() + t);
}, (e, t) => t.getUTCMonth() - e.getUTCMonth() + (t.getUTCFullYear() - e.getUTCFullYear()) * 12, (e) => e.getUTCMonth());
g_.range;
//#endregion
//#region node_modules/d3-time/src/year.js
var __ = Ig((e) => {
	e.setMonth(0, 1), e.setHours(0, 0, 0, 0);
}, (e, t) => {
	e.setFullYear(e.getFullYear() + t);
}, (e, t) => t.getFullYear() - e.getFullYear(), (e) => e.getFullYear());
__.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : Ig((t) => {
	t.setFullYear(Math.floor(t.getFullYear() / e) * e), t.setMonth(0, 1), t.setHours(0, 0, 0, 0);
}, (t, n) => {
	t.setFullYear(t.getFullYear() + n * e);
}), __.range;
var v_ = Ig((e) => {
	e.setUTCMonth(0, 1), e.setUTCHours(0, 0, 0, 0);
}, (e, t) => {
	e.setUTCFullYear(e.getUTCFullYear() + t);
}, (e, t) => t.getUTCFullYear() - e.getUTCFullYear(), (e) => e.getUTCFullYear());
v_.every = (e) => !isFinite(e = Math.floor(e)) || !(e > 0) ? null : Ig((t) => {
	t.setUTCFullYear(Math.floor(t.getUTCFullYear() / e) * e), t.setUTCMonth(0, 1), t.setUTCHours(0, 0, 0, 0);
}, (t, n) => {
	t.setUTCFullYear(t.getUTCFullYear() + n * e);
}), v_.range;
//#endregion
//#region node_modules/d3-time/src/ticks.js
function y_(e, t, n, r, i, a) {
	let o = [
		[
			Gg,
			1,
			Rg
		],
		[
			Gg,
			5,
			5 * Rg
		],
		[
			Gg,
			15,
			15 * Rg
		],
		[
			Gg,
			30,
			30 * Rg
		],
		[
			a,
			1,
			zg
		],
		[
			a,
			5,
			5 * zg
		],
		[
			a,
			15,
			15 * zg
		],
		[
			a,
			30,
			30 * zg
		],
		[
			i,
			1,
			Bg
		],
		[
			i,
			3,
			3 * Bg
		],
		[
			i,
			6,
			6 * Bg
		],
		[
			i,
			12,
			12 * Bg
		],
		[
			r,
			1,
			Vg
		],
		[
			r,
			2,
			2 * Vg
		],
		[
			n,
			1,
			Hg
		],
		[
			t,
			1,
			Ug
		],
		[
			t,
			3,
			3 * Ug
		],
		[
			e,
			1,
			Wg
		]
	];
	function s(e, t, n) {
		let r = t < e;
		r && ([e, t] = [t, e]);
		let i = n && typeof n.range == "function" ? n : c(e, t, n), a = i ? i.range(e, +t + 1) : [];
		return r ? a.reverse() : a;
	}
	function c(t, n, r) {
		let i = Math.abs(n - t) / r, a = Lp(([, , e]) => e).right(o, i);
		if (a === o.length) return e.every(nm(t / Wg, n / Wg, r));
		if (a === 0) return Lg.every(Math.max(nm(t, n, r), 1));
		let [s, c] = o[i / o[a - 1][2] < o[a][2] / i ? a - 1 : a];
		return s.every(c);
	}
	return [s, c];
}
var [b_, x_] = y_(v_, g_, c_, Qg, Yg, qg), [S_, C_] = y_(__, h_, e_, Xg, Jg, Kg);
//#endregion
//#region node_modules/d3-time-format/src/locale.js
function w_(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(-1, e.m, e.d, e.H, e.M, e.S, e.L);
		return t.setFullYear(e.y), t;
	}
	return new Date(e.y, e.m, e.d, e.H, e.M, e.S, e.L);
}
function T_(e) {
	if (0 <= e.y && e.y < 100) {
		var t = new Date(Date.UTC(-1, e.m, e.d, e.H, e.M, e.S, e.L));
		return t.setUTCFullYear(e.y), t;
	}
	return new Date(Date.UTC(e.y, e.m, e.d, e.H, e.M, e.S, e.L));
}
function E_(e, t, n) {
	return {
		y: e,
		m: t,
		d: n,
		H: 0,
		M: 0,
		S: 0,
		L: 0
	};
}
function D_(e) {
	var t = e.dateTime, n = e.date, r = e.time, i = e.periods, a = e.days, o = e.shortDays, s = e.months, c = e.shortMonths, l = N_(i), u = P_(i), d = N_(a), f = P_(a), p = N_(o), m = P_(o), h = N_(s), g = P_(s), _ = N_(c), v = P_(c), y = {
		a: N,
		A: P,
		b: ee,
		B: te,
		c: null,
		d: tv,
		e: tv,
		f: ov,
		g: _v,
		G: yv,
		H: nv,
		I: rv,
		j: iv,
		L: av,
		m: sv,
		M: cv,
		p: ne,
		q: re,
		Q: Hv,
		s: Uv,
		S: lv,
		u: uv,
		U: dv,
		V: pv,
		w: mv,
		W: hv,
		x: null,
		X: null,
		y: gv,
		Y: vv,
		Z: bv,
		"%": Vv
	}, b = {
		a: F,
		A: ie,
		b: ae,
		B: oe,
		c: null,
		d: xv,
		e: xv,
		f: Ev,
		g: Lv,
		G: zv,
		H: Sv,
		I: Cv,
		j: wv,
		L: Tv,
		m: Dv,
		M: Ov,
		p: se,
		q: ce,
		Q: Hv,
		s: Uv,
		S: kv,
		u: Av,
		U: jv,
		V: Nv,
		w: Pv,
		W: Fv,
		x: null,
		X: null,
		y: Iv,
		Y: Rv,
		Z: Bv,
		"%": Vv
	}, x = {
		a: E,
		A: D,
		b: O,
		B: k,
		c: A,
		d: G_,
		e: G_,
		f: Z_,
		g: V_,
		G: B_,
		H: q_,
		I: q_,
		j: K_,
		L: X_,
		m: W_,
		M: J_,
		p: T,
		q: U_,
		Q: $_,
		s: ev,
		S: Y_,
		u: I_,
		U: L_,
		V: R_,
		w: F_,
		W: z_,
		x: j,
		X: M,
		y: V_,
		Y: B_,
		Z: H_,
		"%": Q_
	};
	y.x = S(n, y), y.X = S(r, y), y.c = S(t, y), b.x = S(n, b), b.X = S(r, b), b.c = S(t, b);
	function S(e, t) {
		return function(n) {
			var r = [], i = -1, a = 0, o = e.length, s, c, l;
			for (n instanceof Date || (n = /* @__PURE__ */ new Date(+n)); ++i < o;) e.charCodeAt(i) === 37 && (r.push(e.slice(a, i)), (c = O_[s = e.charAt(++i)]) == null ? c = s === "e" ? " " : "0" : s = e.charAt(++i), (l = t[s]) && (s = l(n, c)), r.push(s), a = i + 1);
			return r.push(e.slice(a, i)), r.join("");
		};
	}
	function C(e, t) {
		return function(n) {
			var r = E_(1900, void 0, 1), i = w(r, e, n += "", 0), a, o;
			if (i != n.length) return null;
			if ("Q" in r) return new Date(r.Q);
			if ("s" in r) return new Date(r.s * 1e3 + ("L" in r ? r.L : 0));
			if (t && !("Z" in r) && (r.Z = 0), "p" in r && (r.H = r.H % 12 + r.p * 12), r.m === void 0 && (r.m = "q" in r ? r.q : 0), "V" in r) {
				if (r.V < 1 || r.V > 53) return null;
				"w" in r || (r.w = 1), "Z" in r ? (a = T_(E_(r.y, 0, 1)), o = a.getUTCDay(), a = o > 4 || o === 0 ? l_.ceil(a) : l_(a), a = Zg.offset(a, (r.V - 1) * 7), r.y = a.getUTCFullYear(), r.m = a.getUTCMonth(), r.d = a.getUTCDate() + (r.w + 6) % 7) : (a = w_(E_(r.y, 0, 1)), o = a.getDay(), a = o > 4 || o === 0 ? t_.ceil(a) : t_(a), a = Xg.offset(a, (r.V - 1) * 7), r.y = a.getFullYear(), r.m = a.getMonth(), r.d = a.getDate() + (r.w + 6) % 7);
			} else ("W" in r || "U" in r) && ("w" in r || (r.w = "u" in r ? r.u % 7 : +("W" in r)), o = "Z" in r ? T_(E_(r.y, 0, 1)).getUTCDay() : w_(E_(r.y, 0, 1)).getDay(), r.m = 0, r.d = "W" in r ? (r.w + 6) % 7 + r.W * 7 - (o + 5) % 7 : r.w + r.U * 7 - (o + 6) % 7);
			return "Z" in r ? (r.H += r.Z / 100 | 0, r.M += r.Z % 100, T_(r)) : w_(r);
		};
	}
	function w(e, t, n, r) {
		for (var i = 0, a = t.length, o = n.length, s, c; i < a;) {
			if (r >= o) return -1;
			if (s = t.charCodeAt(i++), s === 37) {
				if (s = t.charAt(i++), c = x[s in O_ ? t.charAt(i++) : s], !c || (r = c(e, n, r)) < 0) return -1;
			} else if (s != n.charCodeAt(r++)) return -1;
		}
		return r;
	}
	function T(e, t, n) {
		var r = l.exec(t.slice(n));
		return r ? (e.p = u.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function E(e, t, n) {
		var r = p.exec(t.slice(n));
		return r ? (e.w = m.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function D(e, t, n) {
		var r = d.exec(t.slice(n));
		return r ? (e.w = f.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function O(e, t, n) {
		var r = _.exec(t.slice(n));
		return r ? (e.m = v.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function k(e, t, n) {
		var r = h.exec(t.slice(n));
		return r ? (e.m = g.get(r[0].toLowerCase()), n + r[0].length) : -1;
	}
	function A(e, n, r) {
		return w(e, t, n, r);
	}
	function j(e, t, r) {
		return w(e, n, t, r);
	}
	function M(e, t, n) {
		return w(e, r, t, n);
	}
	function N(e) {
		return o[e.getDay()];
	}
	function P(e) {
		return a[e.getDay()];
	}
	function ee(e) {
		return c[e.getMonth()];
	}
	function te(e) {
		return s[e.getMonth()];
	}
	function ne(e) {
		return i[+(e.getHours() >= 12)];
	}
	function re(e) {
		return 1 + ~~(e.getMonth() / 3);
	}
	function F(e) {
		return o[e.getUTCDay()];
	}
	function ie(e) {
		return a[e.getUTCDay()];
	}
	function ae(e) {
		return c[e.getUTCMonth()];
	}
	function oe(e) {
		return s[e.getUTCMonth()];
	}
	function se(e) {
		return i[+(e.getUTCHours() >= 12)];
	}
	function ce(e) {
		return 1 + ~~(e.getUTCMonth() / 3);
	}
	return {
		format: function(e) {
			var t = S(e += "", y);
			return t.toString = function() {
				return e;
			}, t;
		},
		parse: function(e) {
			var t = C(e += "", !1);
			return t.toString = function() {
				return e;
			}, t;
		},
		utcFormat: function(e) {
			var t = S(e += "", b);
			return t.toString = function() {
				return e;
			}, t;
		},
		utcParse: function(e) {
			var t = C(e += "", !0);
			return t.toString = function() {
				return e;
			}, t;
		}
	};
}
var O_ = {
	"-": "",
	_: " ",
	0: "0"
}, k_ = /^\s*\d+/, A_ = /^%/, j_ = /[\\^$*+?|[\]().{}]/g;
function Q(e, t, n) {
	var r = e < 0 ? "-" : "", i = (r ? -e : e) + "", a = i.length;
	return r + (a < n ? Array(n - a + 1).join(t) + i : i);
}
function M_(e) {
	return e.replace(j_, "\\$&");
}
function N_(e) {
	return RegExp("^(?:" + e.map(M_).join("|") + ")", "i");
}
function P_(e) {
	return new Map(e.map((e, t) => [e.toLowerCase(), t]));
}
function F_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 1));
	return r ? (e.w = +r[0], n + r[0].length) : -1;
}
function I_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 1));
	return r ? (e.u = +r[0], n + r[0].length) : -1;
}
function L_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.U = +r[0], n + r[0].length) : -1;
}
function R_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.V = +r[0], n + r[0].length) : -1;
}
function z_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.W = +r[0], n + r[0].length) : -1;
}
function B_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 4));
	return r ? (e.y = +r[0], n + r[0].length) : -1;
}
function V_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.y = +r[0] + (+r[0] > 68 ? 1900 : 2e3), n + r[0].length) : -1;
}
function H_(e, t, n) {
	var r = /^(Z)|([+-]\d\d)(?::?(\d\d))?/.exec(t.slice(n, n + 6));
	return r ? (e.Z = r[1] ? 0 : -(r[2] + (r[3] || "00")), n + r[0].length) : -1;
}
function U_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 1));
	return r ? (e.q = r[0] * 3 - 3, n + r[0].length) : -1;
}
function W_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.m = r[0] - 1, n + r[0].length) : -1;
}
function G_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.d = +r[0], n + r[0].length) : -1;
}
function K_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 3));
	return r ? (e.m = 0, e.d = +r[0], n + r[0].length) : -1;
}
function q_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.H = +r[0], n + r[0].length) : -1;
}
function J_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.M = +r[0], n + r[0].length) : -1;
}
function Y_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 2));
	return r ? (e.S = +r[0], n + r[0].length) : -1;
}
function X_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 3));
	return r ? (e.L = +r[0], n + r[0].length) : -1;
}
function Z_(e, t, n) {
	var r = k_.exec(t.slice(n, n + 6));
	return r ? (e.L = Math.floor(r[0] / 1e3), n + r[0].length) : -1;
}
function Q_(e, t, n) {
	var r = A_.exec(t.slice(n, n + 1));
	return r ? n + r[0].length : -1;
}
function $_(e, t, n) {
	var r = k_.exec(t.slice(n));
	return r ? (e.Q = +r[0], n + r[0].length) : -1;
}
function ev(e, t, n) {
	var r = k_.exec(t.slice(n));
	return r ? (e.s = +r[0], n + r[0].length) : -1;
}
function tv(e, t) {
	return Q(e.getDate(), t, 2);
}
function nv(e, t) {
	return Q(e.getHours(), t, 2);
}
function rv(e, t) {
	return Q(e.getHours() % 12 || 12, t, 2);
}
function iv(e, t) {
	return Q(1 + Xg.count(__(e), e), t, 3);
}
function av(e, t) {
	return Q(e.getMilliseconds(), t, 3);
}
function ov(e, t) {
	return av(e, t) + "000";
}
function sv(e, t) {
	return Q(e.getMonth() + 1, t, 2);
}
function cv(e, t) {
	return Q(e.getMinutes(), t, 2);
}
function lv(e, t) {
	return Q(e.getSeconds(), t, 2);
}
function uv(e) {
	var t = e.getDay();
	return t === 0 ? 7 : t;
}
function dv(e, t) {
	return Q(e_.count(__(e) - 1, e), t, 2);
}
function fv(e) {
	var t = e.getDay();
	return t >= 4 || t === 0 ? i_(e) : i_.ceil(e);
}
function pv(e, t) {
	return e = fv(e), Q(i_.count(__(e), e) + (__(e).getDay() === 4), t, 2);
}
function mv(e) {
	return e.getDay();
}
function hv(e, t) {
	return Q(t_.count(__(e) - 1, e), t, 2);
}
function gv(e, t) {
	return Q(e.getFullYear() % 100, t, 2);
}
function _v(e, t) {
	return e = fv(e), Q(e.getFullYear() % 100, t, 2);
}
function vv(e, t) {
	return Q(e.getFullYear() % 1e4, t, 4);
}
function yv(e, t) {
	var n = e.getDay();
	return e = n >= 4 || n === 0 ? i_(e) : i_.ceil(e), Q(e.getFullYear() % 1e4, t, 4);
}
function bv(e) {
	var t = e.getTimezoneOffset();
	return (t > 0 ? "-" : (t *= -1, "+")) + Q(t / 60 | 0, "0", 2) + Q(t % 60, "0", 2);
}
function xv(e, t) {
	return Q(e.getUTCDate(), t, 2);
}
function Sv(e, t) {
	return Q(e.getUTCHours(), t, 2);
}
function Cv(e, t) {
	return Q(e.getUTCHours() % 12 || 12, t, 2);
}
function wv(e, t) {
	return Q(1 + Zg.count(v_(e), e), t, 3);
}
function Tv(e, t) {
	return Q(e.getUTCMilliseconds(), t, 3);
}
function Ev(e, t) {
	return Tv(e, t) + "000";
}
function Dv(e, t) {
	return Q(e.getUTCMonth() + 1, t, 2);
}
function Ov(e, t) {
	return Q(e.getUTCMinutes(), t, 2);
}
function kv(e, t) {
	return Q(e.getUTCSeconds(), t, 2);
}
function Av(e) {
	var t = e.getUTCDay();
	return t === 0 ? 7 : t;
}
function jv(e, t) {
	return Q(c_.count(v_(e) - 1, e), t, 2);
}
function Mv(e) {
	var t = e.getUTCDay();
	return t >= 4 || t === 0 ? f_(e) : f_.ceil(e);
}
function Nv(e, t) {
	return e = Mv(e), Q(f_.count(v_(e), e) + (v_(e).getUTCDay() === 4), t, 2);
}
function Pv(e) {
	return e.getUTCDay();
}
function Fv(e, t) {
	return Q(l_.count(v_(e) - 1, e), t, 2);
}
function Iv(e, t) {
	return Q(e.getUTCFullYear() % 100, t, 2);
}
function Lv(e, t) {
	return e = Mv(e), Q(e.getUTCFullYear() % 100, t, 2);
}
function Rv(e, t) {
	return Q(e.getUTCFullYear() % 1e4, t, 4);
}
function zv(e, t) {
	var n = e.getUTCDay();
	return e = n >= 4 || n === 0 ? f_(e) : f_.ceil(e), Q(e.getUTCFullYear() % 1e4, t, 4);
}
function Bv() {
	return "+0000";
}
function Vv() {
	return "%";
}
function Hv(e) {
	return +e;
}
function Uv(e) {
	return Math.floor(e / 1e3);
}
//#endregion
//#region node_modules/d3-time-format/src/defaultLocale.js
var Wv, Gv, Kv;
qv({
	dateTime: "%x, %X",
	date: "%-m/%-d/%Y",
	time: "%-I:%M:%S %p",
	periods: ["AM", "PM"],
	days: [
		"Sunday",
		"Monday",
		"Tuesday",
		"Wednesday",
		"Thursday",
		"Friday",
		"Saturday"
	],
	shortDays: [
		"Sun",
		"Mon",
		"Tue",
		"Wed",
		"Thu",
		"Fri",
		"Sat"
	],
	months: [
		"January",
		"February",
		"March",
		"April",
		"May",
		"June",
		"July",
		"August",
		"September",
		"October",
		"November",
		"December"
	],
	shortMonths: [
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec"
	]
});
function qv(e) {
	return Wv = D_(e), Gv = Wv.format, Wv.parse, Kv = Wv.utcFormat, Wv.utcParse, Wv;
}
//#endregion
//#region node_modules/d3-scale/src/time.js
function Jv(e) {
	return new Date(e);
}
function Yv(e) {
	return e instanceof Date ? +e : +/* @__PURE__ */ new Date(+e);
}
function Xv(e, t, n, r, i, a, o, s, c, l) {
	var u = Mh(), d = u.invert, f = u.domain, p = l(".%L"), m = l(":%S"), h = l("%I:%M"), g = l("%I %p"), _ = l("%a %d"), v = l("%b %d"), y = l("%B"), b = l("%Y");
	function x(e) {
		return (c(e) < e ? p : s(e) < e ? m : o(e) < e ? h : a(e) < e ? g : r(e) < e ? i(e) < e ? _ : v : n(e) < e ? y : b)(e);
	}
	return u.invert = function(e) {
		return new Date(d(e));
	}, u.domain = function(e) {
		return arguments.length ? f(Array.from(e, Yv)) : f().map(Jv);
	}, u.ticks = function(t) {
		var n = f();
		return e(n[0], n[n.length - 1], t == null ? 10 : t);
	}, u.tickFormat = function(e, t) {
		return t == null ? x : l(t);
	}, u.nice = function(e) {
		var n = f();
		return (!e || typeof e.range != "function") && (e = t(n[0], n[n.length - 1], e == null ? 10 : e)), e ? f(sg(n, e)) : u;
	}, u.copy = function() {
		return Ah(u, Xv(e, t, n, r, i, a, o, s, c, l));
	}, u;
}
function Zv() {
	return um.apply(Xv(S_, C_, __, h_, e_, Xg, Jg, Kg, Gg, Gv).domain([new Date(2e3, 0, 1), new Date(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/utcTime.js
function Qv() {
	return um.apply(Xv(b_, x_, v_, g_, c_, Zg, Yg, qg, Gg, Kv).domain([Date.UTC(2e3, 0, 1), Date.UTC(2e3, 0, 2)]), arguments);
}
//#endregion
//#region node_modules/d3-scale/src/sequential.js
function $v() {
	var e = 0, t = 1, n, r, i, a, o = Th, s = !1, c;
	function l(e) {
		return e == null || isNaN(e = +e) ? c : o(i === 0 ? .5 : (e = (a(e) - n) * i, s ? Math.max(0, Math.min(1, e)) : e));
	}
	l.domain = function(o) {
		return arguments.length ? ([e, t] = o, n = a(e = +e), r = a(t = +t), i = n === r ? 0 : 1 / (r - n), l) : [e, t];
	}, l.clamp = function(e) {
		return arguments.length ? (s = !!e, l) : s;
	}, l.interpolator = function(e) {
		return arguments.length ? (o = e, l) : o;
	};
	function u(e) {
		return function(t) {
			var n, r;
			return arguments.length ? ([n, r] = t, o = e(n, r), l) : [o(0), o(1)];
		};
	}
	return l.range = u(yh), l.rangeRound = u(bh), l.unknown = function(e) {
		return arguments.length ? (c = e, l) : c;
	}, function(o) {
		return a = o, n = o(e), r = o(t), i = n === r ? 0 : 1 / (r - n), l;
	};
}
function ey(e, t) {
	return t.domain(e.domain()).interpolator(e.interpolator()).clamp(e.clamp()).unknown(e.unknown());
}
function ty() {
	var e = ig($v()(Th));
	return e.copy = function() {
		return ey(e, ty());
	}, dm.apply(e, arguments);
}
function ny() {
	var e = gg($v()).domain([1, 10]);
	return e.copy = function() {
		return ey(e, ny()).base(e.base());
	}, dm.apply(e, arguments);
}
function ry() {
	var e = bg($v());
	return e.copy = function() {
		return ey(e, ry()).constant(e.constant());
	}, dm.apply(e, arguments);
}
function iy() {
	var e = Tg($v());
	return e.copy = function() {
		return ey(e, iy()).exponent(e.exponent());
	}, dm.apply(e, arguments);
}
function ay() {
	return iy.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/d3-scale/src/sequentialQuantile.js
function oy() {
	var e = [], t = Th;
	function n(n) {
		if (n != null && !isNaN(n = +n)) return t((Hp(e, n, 1) - 1) / (e.length - 1));
	}
	return n.domain = function(t) {
		if (!arguments.length) return e.slice();
		e = [];
		for (let n of t) n != null && !isNaN(n = +n) && e.push(n);
		return e.sort(Fp), n;
	}, n.interpolator = function(e) {
		return arguments.length ? (t = e, n) : t;
	}, n.range = function() {
		return e.map((n, r) => t(r / (e.length - 1)));
	}, n.quantiles = function(t) {
		return Array.from({ length: t + 1 }, (n, r) => sm(e, r / t));
	}, n.copy = function() {
		return oy(t).domain(e);
	}, dm.apply(n, arguments);
}
//#endregion
//#region node_modules/d3-scale/src/diverging.js
function sy() {
	var e = 0, t = .5, n = 1, r = 1, i, a, o, s, c, l = Th, u, d = !1, f;
	function p(e) {
		return isNaN(e = +e) ? f : (e = .5 + ((e = +u(e)) - a) * (r * e < r * a ? s : c), l(d ? Math.max(0, Math.min(1, e)) : e));
	}
	p.domain = function(l) {
		return arguments.length ? ([e, t, n] = l, i = u(e = +e), a = u(t = +t), o = u(n = +n), s = i === a ? 0 : .5 / (a - i), c = a === o ? 0 : .5 / (o - a), r = a < i ? -1 : 1, p) : [
			e,
			t,
			n
		];
	}, p.clamp = function(e) {
		return arguments.length ? (d = !!e, p) : d;
	}, p.interpolator = function(e) {
		return arguments.length ? (l = e, p) : l;
	};
	function m(e) {
		return function(t) {
			var n, r, i;
			return arguments.length ? ([n, r, i] = t, l = xh(e, [
				n,
				r,
				i
			]), p) : [
				l(0),
				l(.5),
				l(1)
			];
		};
	}
	return p.range = m(yh), p.rangeRound = m(bh), p.unknown = function(e) {
		return arguments.length ? (f = e, p) : f;
	}, function(l) {
		return u = l, i = l(e), a = l(t), o = l(n), s = i === a ? 0 : .5 / (a - i), c = a === o ? 0 : .5 / (o - a), r = a < i ? -1 : 1, p;
	};
}
function cy() {
	var e = ig(sy()(Th));
	return e.copy = function() {
		return ey(e, cy());
	}, dm.apply(e, arguments);
}
function ly() {
	var e = gg(sy()).domain([
		.1,
		1,
		10
	]);
	return e.copy = function() {
		return ey(e, ly()).base(e.base());
	}, dm.apply(e, arguments);
}
function uy() {
	var e = bg(sy());
	return e.copy = function() {
		return ey(e, uy()).constant(e.constant());
	}, dm.apply(e, arguments);
}
function dy() {
	var e = Tg(sy());
	return e.copy = function() {
		return ey(e, dy()).exponent(e.exponent());
	}, dm.apply(e, arguments);
}
function fy() {
	return dy.apply(null, arguments).exponent(.5);
}
//#endregion
//#region node_modules/victory-vendor/es/d3-scale.js
var py = /* @__PURE__ */ s({
	scaleBand: () => mm,
	scaleDiverging: () => cy,
	scaleDivergingLog: () => ly,
	scaleDivergingPow: () => dy,
	scaleDivergingSqrt: () => fy,
	scaleDivergingSymlog: () => uy,
	scaleIdentity: () => og,
	scaleImplicit: () => fm,
	scaleLinear: () => ag,
	scaleLog: () => _g,
	scaleOrdinal: () => pm,
	scalePoint: () => gm,
	scalePow: () => Eg,
	scaleQuantile: () => jg,
	scaleQuantize: () => Mg,
	scaleRadial: () => Ag,
	scaleSequential: () => ty,
	scaleSequentialLog: () => ny,
	scaleSequentialPow: () => iy,
	scaleSequentialQuantile: () => oy,
	scaleSequentialSqrt: () => ay,
	scaleSequentialSymlog: () => ry,
	scaleSqrt: () => Dg,
	scaleSymlog: () => xg,
	scaleThreshold: () => Ng,
	scaleTime: () => Zv,
	scaleUtc: () => Qv,
	tickFormat: () => rg
});
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineConfiguredScale.js
function my(e) {
	var t = py;
	if (e in t && typeof t[e] == "function") return t[e]();
	var n = `scale${Rt(e)}`;
	if (n in t && typeof t[n] == "function") return t[n]();
}
function hy(e, t, n) {
	if (typeof e == "function") return e.copy().domain(t).range(n);
	if (e != null) {
		var r = my(e);
		if (r != null) return r.domain(t).range(n), r;
	}
}
function gy(e, t, n, r) {
	if (!(n == null || r == null)) return typeof e.scale == "function" ? hy(e.scale, n, r) : hy(t, n, r);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineRealScaleType.js
function _y(e) {
	return `scale${Rt(e)}`;
}
function vy(e) {
	return _y(e) in py;
}
var yy = (e, t, n) => {
	if (e != null) {
		var r = e.scale, i = e.type;
		if (r === "auto") return i === "category" && n && (n.indexOf("LineChart") >= 0 || n.indexOf("AreaChart") >= 0 || n.indexOf("ComposedChart") >= 0 && !t) ? "point" : i === "category" ? "band" : "linear";
		if (typeof r == "string") return vy(r) ? r : "point";
	}
};
//#endregion
//#region node_modules/recharts/es6/util/scale/createCategoricalInverse.js
function by(e, t) {
	for (var n = 0, r = e.length, i = e[0] < e[e.length - 1]; n < r;) {
		var a = Math.floor((n + r) / 2);
		(i ? e[a] < t : e[a] > t) ? n = a + 1 : r = a;
	}
	return n;
}
function xy(e, t) {
	if (e) {
		var n = t == null ? e.domain() : t, r = n.map((t) => {
			var n;
			return (n = e(t)) == null ? 0 : n;
		}), i = e.range();
		if (!(n.length === 0 || i.length < 2)) return (e) => {
			var t, i, a = by(r, e);
			if (a <= 0) return n[0];
			if (a >= n.length) return n[n.length - 1];
			var o = (t = r[a - 1]) == null ? 0 : t, s = (i = r[a]) == null ? 0 : i;
			return Math.abs(e - o) <= Math.abs(e - s) ? n[a - 1] : n[a];
		};
	}
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineInverseScaleFunction.js
function Sy(e) {
	if (e != null) return "invert" in e && typeof e.invert == "function" ? e.invert.bind(e) : xy(e, void 0);
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/axisSelectors.js
function Cy(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function wy(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Cy(Object(n), !0).forEach(function(t) {
			Ty(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Cy(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Ty(e, t, n) {
	return (t = Ey(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Ey(e) {
	var t = Dy(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Dy(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Oy(e, t) {
	return Ny(e) || My(e, t) || Ay(e, t) || ky();
}
function ky() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Ay(e, t) {
	if (e) {
		if (typeof e == "string") return jy(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? jy(e, t) : void 0;
	}
}
function jy(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function My(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Ny(e) {
	if (Array.isArray(e)) return e;
}
var Py = [0, "auto"], Fy = {
	allowDataOverflow: !1,
	allowDecimals: !0,
	allowDuplicatedCategory: !0,
	angle: 0,
	dataKey: void 0,
	domain: void 0,
	height: 30,
	hide: !0,
	id: 0,
	includeHidden: !1,
	interval: "preserveEnd",
	minTickGap: 5,
	mirror: !1,
	name: void 0,
	orientation: "bottom",
	padding: {
		left: 0,
		right: 0
	},
	reversed: !1,
	scale: "auto",
	tick: !0,
	tickCount: 5,
	tickFormatter: void 0,
	ticks: void 0,
	type: "category",
	unit: void 0,
	niceTicks: "auto"
}, Iy = (e, t) => e.cartesianAxis.xAxis[t], Ly = (e, t) => {
	var n = Iy(e, t);
	return n == null ? Fy : n;
}, Ry = {
	allowDataOverflow: !1,
	allowDecimals: !0,
	allowDuplicatedCategory: !0,
	angle: 0,
	dataKey: void 0,
	domain: Py,
	hide: !0,
	id: 0,
	includeHidden: !1,
	interval: "preserveEnd",
	minTickGap: 5,
	mirror: !1,
	name: void 0,
	orientation: "left",
	padding: {
		top: 0,
		bottom: 0
	},
	reversed: !1,
	scale: "auto",
	tick: !0,
	tickCount: 5,
	tickFormatter: void 0,
	ticks: void 0,
	type: "number",
	unit: void 0,
	niceTicks: "auto",
	width: 60
}, zy = (e, t) => e.cartesianAxis.yAxis[t], By = (e, t) => {
	var n = zy(e, t);
	return n == null ? Ry : n;
}, Vy = {
	domain: [0, "auto"],
	includeHidden: !1,
	reversed: !1,
	allowDataOverflow: !1,
	allowDuplicatedCategory: !1,
	dataKey: void 0,
	id: 0,
	name: "",
	range: [64, 64],
	scale: "auto",
	type: "number",
	unit: ""
}, Hy = (e, t) => {
	var n = e.cartesianAxis.zAxis[t];
	return n == null ? Vy : n;
}, Uy = (e, t, n) => {
	switch (t) {
		case "xAxis": return Ly(e, n);
		case "yAxis": return By(e, n);
		case "zAxis": return Hy(e, n);
		case "angleAxis": return mp(e, n);
		case "radiusAxis": return hp(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, Wy = (e, t, n) => {
	switch (t) {
		case "xAxis": return Ly(e, n);
		case "yAxis": return By(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, Gy = (e, t, n) => {
	switch (t) {
		case "xAxis": return Ly(e, n);
		case "yAxis": return By(e, n);
		case "angleAxis": return mp(e, n);
		case "radiusAxis": return hp(e, n);
		default: throw Error(`Unexpected axis type: ${t}`);
	}
}, Ky = (e) => e.graphicalItems.cartesianItems.some((e) => e.type === "bar") || e.graphicalItems.polarItems.some((e) => e.type === "radialBar");
function qy(e, t) {
	return (n) => {
		switch (e) {
			case "xAxis": return "xAxisId" in n && n.xAxisId === t;
			case "yAxis": return "yAxisId" in n && n.yAxisId === t;
			case "zAxis": return "zAxisId" in n && n.zAxisId === t;
			case "angleAxis": return "angleAxisId" in n && n.angleAxisId === t;
			case "radiusAxis": return "radiusAxisId" in n && n.radiusAxisId === t;
			default: return !1;
		}
	};
}
var Jy = (e) => e.graphicalItems.cartesianItems, Yy = B([Cp, wp], qy), Xy = (e, t, n) => e.filter(n).filter((e) => (t == null ? void 0 : t.includeHidden) === !0 || !e.hide), Zy = B([
	Jy,
	Uy,
	Yy
], Xy, { memoizeOptions: { resultEqualityCheck: kp } }), Qy = B([Zy], (e) => e.filter((e) => e.type === "area" || e.type === "bar").filter(Dp)), $y = (e) => e.filter((e) => !("stackId" in e) || e.stackId === void 0), eb = B([Zy], $y), tb = (e) => e.map((e) => e.data).filter(Boolean).flat(1), nb = B([Zy], (e) => e.some((e) => !e.data)), rb = B([Zy], tb, { memoizeOptions: { resultEqualityCheck: kp } }), ib = (e, t) => {
	var n = t.chartData, r = n === void 0 ? [] : n, i = t.dataStartIndex, a = t.dataEndIndex;
	return e.length > 0 ? e : r.slice(i, a + 1);
}, ab = B([rb, _f], ib), ob = (e, t, n) => (t == null ? void 0 : t.dataKey) == null ? n.length > 0 ? n.map((e) => e.dataKey).flatMap((t) => e.map((e) => ({ value: ns(e, t) }))) : e.map((e) => ({ value: e })) : e.map((e) => ({ value: ns(e, t.dataKey) })), sb = (e, t, n, r, i, a) => {
	var o = r.chartData, s = o === void 0 ? [] : o, c = r.dataStartIndex, l = r.dataEndIndex, u = ob(e, t, n);
	return i && (t == null ? void 0 : t.dataKey) != null && a.length > 0 ? [...s.slice(c, l + 1).map((e) => ({ value: ns(e, t.dataKey) })).filter((e) => e.value != null), ...u] : u;
}, cb = B([
	ab,
	Uy,
	Zy,
	_f,
	nb,
	rb
], sb);
function lb(e) {
	if (At(e) || e instanceof Date) {
		var t = Number(e);
		if (q(t)) return t;
	}
}
function ub(e) {
	if (Array.isArray(e)) {
		var t = [lb(e[0]), lb(e[1])];
		return Df(t) ? t : void 0;
	}
	var n = lb(e);
	if (n != null) return [n, n];
}
function db(e) {
	return e.map(lb).filter(zt);
}
function fb(e, t) {
	var n = lb(e), r = lb(t);
	return n == null && r == null ? 0 : n == null ? -1 : r == null ? 1 : n - r;
}
var pb = B([cb], (e) => e == null ? void 0 : e.map((e) => e.value).sort(fb));
function mb(e, t) {
	switch (e) {
		case "xAxis": return t.direction === "x";
		case "yAxis": return t.direction === "y";
		default: return !1;
	}
}
function hb(e, t, n) {
	if (!n || !n.length) return [];
	var r;
	if (typeof t == "number" && !Ot(t)) r = t;
	else if (Array.isArray(t)) {
		var i = db(t);
		i.length > 0 && (r = Math.max(...i));
	}
	return r == null ? [] : db(n.flatMap((t) => {
		var n = ns(e, t.dataKey), i, a;
		if (Array.isArray(n)) {
			var o = Oy(n, 2);
			i = o[0], a = o[1];
		} else i = a = n;
		if (!(!q(i) || !q(a))) return [r - i, r + a];
	}));
}
var gb = (e) => Gy(e, jp(e), Mp(e)), _b = B([gb], (e) => e == null ? void 0 : e.dataKey), vb = B([
	Qy,
	_f,
	gb
], Ep), yb = (e, t, n, r) => {
	var i = t.reduce((e, t) => {
		if (t.stackId == null) return e;
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, {});
	return Object.fromEntries(Object.entries(i).map((t) => {
		var i = Oy(t, 2), a = i[0], o = i[1], s = r ? [...o].reverse() : o;
		return [a, {
			stackedData: ss(e, s.map(Tp), n),
			graphicalItems: s
		}];
	}));
}, bb = B([
	vb,
	Qy,
	Xf,
	Zf
], yb), xb = (e, t, n, r) => {
	var i = t.dataStartIndex, a = t.dataEndIndex;
	if (r == null && n !== "zAxis") return ps(e, i, a);
}, Sb = B([Uy], (e) => e.allowDataOverflow), Cb = (e) => {
	var t;
	if (e == null || !("domain" in e)) return Py;
	if (e.domain != null) return e.domain;
	if ("ticks" in e && e.ticks != null) {
		if (e.type === "number") {
			var n = db(e.ticks);
			return [Math.min(...n), Math.max(...n)];
		}
		if (e.type === "category") return e.ticks.map(String);
	}
	return (t = e == null ? void 0 : e.domain) == null ? Py : t;
}, wb = B([Uy], Cb), Tb = B([wb, Sb], kf), Eb = B([
	bb,
	hf,
	Cp,
	Tb
], xb, { memoizeOptions: { resultEqualityCheck: Op } }), Db = (e) => e.errorBars, Ob = (e, t, n) => e.flatMap((e) => t[e.id]).filter(Boolean).filter((e) => mb(n, e)), kb = function() {
	var e = [...arguments].filter(Boolean);
	if (e.length !== 0) {
		var t = e.flat();
		return [Math.min(...t), Math.max(...t)];
	}
}, Ab = function(e, t, n, r, i) {
	var a = arguments.length > 5 && arguments[5] !== void 0 ? arguments[5] : [], o, s;
	if (n.length > 0 && n.forEach((e) => {
		var n, c = e.data == null ? a : [...e.data], l = (n = r[e.id]) == null ? void 0 : n.filter((e) => mb(i, e));
		c.forEach((n) => {
			var r, i = ns(n, (r = t.dataKey) == null ? e.dataKey : r), a = hb(n, i, l);
			if (a.length >= 2) {
				var c = Math.min(...a), u = Math.max(...a);
				(o == null || c < o) && (o = c), (s == null || u > s) && (s = u);
			}
			var d = ub(i);
			d != null && (o = o == null ? d[0] : Math.min(o, d[0]), s = s == null ? d[1] : Math.max(s, d[1]));
		});
	}), (t == null ? void 0 : t.dataKey) != null && n.length === 0 && e.forEach((e) => {
		var n = ub(ns(e, t.dataKey));
		n != null && (o = o == null ? n[0] : Math.min(o, n[0]), s = s == null ? n[1] : Math.max(s, n[1]));
	}), q(o) && q(s)) return [o, s];
}, jb = B([
	ab,
	Uy,
	eb,
	Db,
	Cp,
	yf
], Ab, { memoizeOptions: { resultEqualityCheck: Op } });
function Mb(e) {
	var t = e.value;
	if (At(t) || t instanceof Date) return t;
}
var Nb = (e, t, n) => {
	var r = e.map(Mb).filter((e) => e != null);
	return n && (t.dataKey == null || t.allowDuplicatedCategory && Pt(r)) ? mf(0, e.length) : t.allowDuplicatedCategory ? r : Array.from(new Set(r));
}, Pb = (e) => e.referenceElements.dots, Fb = (e, t, n) => e.filter((e) => e.ifOverflow === "extendDomain").filter((e) => t === "xAxis" ? e.xAxisId === n : e.yAxisId === n), Ib = B([
	Pb,
	Cp,
	wp
], Fb), Lb = (e) => e.referenceElements.areas, Rb = B([
	Lb,
	Cp,
	wp
], Fb), zb = (e) => e.referenceElements.lines, Bb = B([
	zb,
	Cp,
	wp
], Fb), Vb = (e, t) => {
	if (e != null) {
		var n = db(e.map((e) => t === "xAxis" ? e.x : e.y));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Hb = B(Ib, Cp, Vb), Ub = (e, t) => {
	if (e != null) {
		var n = db(e.flatMap((e) => [t === "xAxis" ? e.x1 : e.y1, t === "xAxis" ? e.x2 : e.y2]));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Wb = B([Rb, Cp], Ub);
function Gb(e) {
	var t;
	if (e.x != null) return db([e.x]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.x);
	return n == null || n.length === 0 ? [] : db(n);
}
function Kb(e) {
	var t;
	if (e.y != null) return db([e.y]);
	var n = (t = e.segment) == null ? void 0 : t.map((e) => e.y);
	return n == null || n.length === 0 ? [] : db(n);
}
var qb = (e, t) => {
	if (e != null) {
		var n = e.flatMap((e) => t === "xAxis" ? Gb(e) : Kb(e));
		if (n.length !== 0) return [Math.min(...n), Math.max(...n)];
	}
}, Jb = B(Hb, B([Bb, Cp], qb), Wb, (e, t, n) => kb(e, n, t)), Yb = (e, t, n, r, i, a, o, s, c) => {
	if (n != null) return n;
	var l = o === "vertical" && s === "xAxis" || o === "horizontal" && s === "yAxis" ? kb(r, a, i) : kb(a, i), u = Af(t, l, e.allowDataOverflow);
	return u == null && e.allowDataOverflow && l == null && c != null ? c : u;
}, Xb = B([
	Uy,
	wb,
	Tb,
	Eb,
	jb,
	Jb,
	Y,
	Cp,
	B([Uy], (e) => {
		if (!(e == null || e.type !== "number" || !("ticks" in e) || e.ticks == null)) {
			var t = db(e.ticks);
			if (t.length !== 0) return [Math.min(...t), Math.max(...t)];
		}
	}, { memoizeOptions: { resultEqualityCheck: Op } })
], Yb, { memoizeOptions: { resultEqualityCheck: Op } }), Zb = [0, 1], Qb = (e, t, n, r, i, a, o) => {
	if (!((e == null || n == null || n.length === 0) && o === void 0)) {
		var s = e.dataKey, c = e.type, l = is(t, a);
		if (l && s == null) {
			var u;
			return mf(0, (u = n == null ? void 0 : n.length) == null ? 0 : u);
		}
		return c === "category" ? Nb(r, e, l) : i === "expand" && !l ? Zb : o;
	}
}, $b = B([
	Uy,
	Y,
	ab,
	cb,
	Xf,
	Cp,
	Xb
], Qb), ex = B([
	Uy,
	Ky,
	Qf
], yy), tx = (e, t, n) => {
	var r = t.niceTicks;
	if (r !== "none") {
		var i = Cb(t), a = Array.isArray(i) && (i[0] === "auto" || i[1] === "auto");
		if ((r === "snap125" || r === "adaptive") && t != null && t.tickCount && Df(e)) {
			if (a) return Wf(e, t.tickCount, t.allowDecimals, r);
			if (t.type === "number") return Gf(e, t.tickCount, t.allowDecimals, r);
		}
		if (r === "auto" && n === "linear" && t != null && t.tickCount) {
			if (a && Df(e)) return Wf(e, t.tickCount, t.allowDecimals, "adaptive");
			if (t.type === "number" && Df(e)) return Gf(e, t.tickCount, t.allowDecimals, "adaptive");
		}
	}
}, nx = B([
	$b,
	Gy,
	ex
], tx), rx = (e, t, n, r) => {
	if (r !== "angleAxis" && (e == null ? void 0 : e.type) === "number" && Df(t) && Array.isArray(n) && n.length > 0) {
		var i, a, o = t[0], s = (i = n[0]) == null ? 0 : i, c = t[1], l = (a = n[n.length - 1]) == null ? 0 : a;
		return [Math.min(o, s), Math.max(c, l)];
	}
	return t;
}, ix = B([
	Uy,
	$b,
	nx,
	Cp
], rx), ax = B(B(cb, Uy, (e, t) => {
	if (!(!t || t.type !== "number")) {
		var n = Infinity, r = Array.from(db(e.map((e) => e.value))).sort((e, t) => e - t), i = r[0], a = r[r.length - 1];
		if (i == null || a == null) return Infinity;
		var o = a - i;
		if (o === 0) return Infinity;
		for (var s = 0; s < r.length - 1; s++) {
			var c = r[s], l = r[s + 1];
			if (!(c == null || l == null)) {
				var u = l - c;
				n = Math.min(n, u);
			}
		}
		return n / o;
	}
}), Y, Jf, Rs, (e, t, n, r, i) => i, (e, t, n, r, i) => {
	if (!q(e)) return 0;
	var a = t === "vertical" ? r.height : r.width;
	if (i === "gap") return e * a / 2;
	if (i === "no-gap") {
		var o = Nt(n, e * a), s = e * a / 2;
		return s - o - (s - o) / a * o;
	}
	return 0;
}), ox = (e, t, n) => {
	var r = Ly(e, t);
	return r == null || typeof r.padding != "string" ? 0 : ax(e, "xAxis", t, n, r.padding);
}, sx = (e, t, n) => {
	var r = By(e, t);
	return r == null || typeof r.padding != "string" ? 0 : ax(e, "yAxis", t, n, r.padding);
}, cx = B(Ly, ox, (e, t) => {
	var n, r;
	if (e == null) return {
		left: 0,
		right: 0
	};
	var i = e.padding;
	return typeof i == "string" ? {
		left: t,
		right: t
	} : {
		left: ((n = i.left) == null ? 0 : n) + t,
		right: ((r = i.right) == null ? 0 : r) + t
	};
}), lx = B(By, sx, (e, t) => {
	var n, r;
	if (e == null) return {
		top: 0,
		bottom: 0
	};
	var i = e.padding;
	return typeof i == "string" ? {
		top: t,
		bottom: t
	} : {
		top: ((n = i.top) == null ? 0 : n) + t,
		bottom: ((r = i.bottom) == null ? 0 : r) + t
	};
}), ux = B([
	Rs,
	cx,
	Ws,
	Us,
	(e, t, n) => n
], (e, t, n, r, i) => {
	var a = r.padding;
	return i ? [a.left, n.width - a.right] : [e.left + t.left, e.left + e.width - t.right];
}), dx = B([
	Rs,
	Y,
	lx,
	Ws,
	Us,
	(e, t, n) => n
], (e, t, n, r, i, a) => {
	var o = i.padding;
	return a ? [r.height - o.bottom, o.top] : t === "horizontal" ? [e.top + e.height - n.bottom, e.top + n.top] : [e.top + n.top, e.top + e.height - n.bottom];
}), fx = (e, t, n, r) => {
	var i;
	switch (t) {
		case "xAxis": return ux(e, n, r);
		case "yAxis": return dx(e, n, r);
		case "zAxis": return (i = Hy(e, n)) == null ? void 0 : i.range;
		case "angleAxis": return bp(e);
		case "radiusAxis": return xp(e, n);
		default: return;
	}
}, px = B([Uy, fx], ap), mx = B([
	Uy,
	ex,
	B([ex, ix], Pp),
	px
], gy), hx = (e, t, n, r) => {
	if (!(n == null || n.dataKey == null)) {
		var i = n.type, a = n.scale;
		if (is(e, r) && (i === "number" || a !== "auto")) return t.map((e) => e.value);
	}
}, gx = B([
	Y,
	cb,
	Gy,
	Cp
], hx), _x = B([mx], Np);
B([mx], Sy), B([mx, pb], xy), B([
	Zy,
	Db,
	Cp
], Ob);
function vx(e, t) {
	return e.id < t.id ? -1 : +(e.id > t.id);
}
var yx = (e, t) => t, bx = (e, t, n) => n, xx = B(Ts, yx, bx, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(vx)), Sx = B(Es, yx, bx, (e, t, n) => e.filter((e) => e.orientation === t).filter((e) => e.mirror === n).sort(vx)), Cx = (e, t) => ({
	width: e.width,
	height: t.height
}), wx = (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
}), Tx = B(Rs, Ly, Cx), Ex = (e, t, n) => {
	switch (t) {
		case "top": return e.top;
		case "bottom": return n - e.bottom;
		default: return 0;
	}
}, Dx = (e, t, n) => {
	switch (t) {
		case "left": return e.left;
		case "right": return n - e.right;
		default: return 0;
	}
}, Ox = B(Ss, Rs, xx, yx, bx, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = Cx(t, n);
		o == null && (o = Ex(t, r, e));
		var c = r === "top" && !i || r === "bottom" && i;
		a[n.id] = o - Number(c) * s.height, o += (c ? -1 : 1) * s.height;
	}), a;
}), kx = B(xs, Rs, Sx, yx, bx, (e, t, n, r, i) => {
	var a = {}, o;
	return n.forEach((n) => {
		var s = wx(t, n);
		o == null && (o = Dx(t, r, e));
		var c = r === "left" && !i || r === "right" && i;
		a[n.id] = o - Number(c) * s.width, o += (c ? -1 : 1) * s.width;
	}), a;
}), Ax = B([
	Rs,
	Ly,
	(e, t) => {
		var n = Ly(e, t);
		if (n != null) return Ox(e, n.orientation, n.mirror);
	},
	(e, t) => t
], (e, t, n, r) => {
	if (t != null) {
		var i = n == null ? void 0 : n[r];
		return i == null ? {
			x: e.left,
			y: 0
		} : {
			x: e.left,
			y: i
		};
	}
}), jx = B([
	Rs,
	By,
	(e, t) => {
		var n = By(e, t);
		if (n != null) return kx(e, n.orientation, n.mirror);
	},
	(e, t) => t
], (e, t, n, r) => {
	if (t != null) {
		var i = n == null ? void 0 : n[r];
		return i == null ? {
			x: 0,
			y: e.top
		} : {
			x: i,
			y: e.top
		};
	}
}), Mx = B(Rs, By, (e, t) => ({
	width: typeof t.width == "number" ? t.width : 60,
	height: e.height
})), Nx = (e, t, n) => {
	switch (t) {
		case "xAxis": return Tx(e, n).width;
		case "yAxis": return Mx(e, n).height;
		default: return;
	}
}, Px = (e, t, n, r) => {
	if (n != null) {
		var i = n.allowDuplicatedCategory, a = n.type, o = n.dataKey, s = is(e, r), c = t.map((e) => e.value), l = c.filter((e) => e != null);
		if (o && s && a === "category" && i && Pt(l)) return c;
	}
}, Fx = B([
	Y,
	cb,
	Uy,
	Cp
], Px);
B([
	Y,
	Wy,
	ex,
	_x,
	Fx,
	gx,
	fx,
	nx,
	Cp
], (e, t, n, r, i, a, o, s, c) => {
	if (t != null) {
		var l = is(e, c);
		return {
			angle: t.angle,
			interval: t.interval,
			minTickGap: t.minTickGap,
			orientation: t.orientation,
			tick: t.tick,
			tickCount: t.tickCount,
			tickFormatter: t.tickFormatter,
			ticks: t.ticks,
			type: t.type,
			unit: t.unit,
			axisType: c,
			categoricalDomain: a,
			duplicateDomain: i,
			isCategorical: l,
			niceTicks: s,
			range: o,
			realScaleType: n,
			scale: r
		};
	}
});
var Ix = B([
	Y,
	Gy,
	ex,
	_x,
	nx,
	fx,
	Fx,
	gx,
	Cp
], (e, t, n, r, i, a, o, s, c) => {
	if (!(t == null || r == null)) {
		var l = is(e, c), u = t.type, d = t.ticks, f = t.tickCount, p = n === "scaleBand" && typeof r.bandwidth == "function" ? r.bandwidth() / 2 : 2, m = u === "category" && r.bandwidth ? r.bandwidth() / p : 0;
		m = c === "angleAxis" && a != null && a.length >= 2 ? Dt(a[0] - a[1]) * 2 * m : m;
		var h = d || i;
		return h ? h.map((e, t) => {
			var n = o ? o.indexOf(e) : e, i = r.map(n);
			return q(i) ? {
				index: t,
				coordinate: i + m,
				value: e,
				offset: m
			} : null;
		}).filter(zt) : l && s ? s.map((e, t) => {
			var n = r.map(e);
			return q(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(zt) : r.ticks ? r.ticks(f).map((e, t) => {
			var n = r.map(e);
			return q(n) ? {
				coordinate: n + m,
				value: e,
				index: t,
				offset: m
			} : null;
		}).filter(zt) : r.domain().map((e, t) => {
			var n = r.map(e);
			return q(n) ? {
				coordinate: n + m,
				value: o ? o[e] : e,
				index: t,
				offset: m
			} : null;
		}).filter(zt);
	}
}), Lx = B([
	Y,
	Gy,
	_x,
	fx,
	Fx,
	gx,
	Cp
], (e, t, n, r, i, a, o) => {
	if (!(t == null || n == null || r == null || r[0] === r[1])) {
		var s = is(e, o), c = t.tickCount, l = 0;
		return l = o === "angleAxis" && (r == null ? void 0 : r.length) >= 2 ? Dt(r[0] - r[1]) * 2 * l : l, s && a ? a.map((e, t) => {
			var r = n.map(e);
			return q(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(zt) : n.ticks ? n.ticks(c).map((e, t) => {
			var r = n.map(e);
			return q(r) ? {
				coordinate: r + l,
				value: e,
				index: t,
				offset: l
			} : null;
		}).filter(zt) : n.domain().map((e, t) => {
			var r = n.map(e);
			return q(r) ? {
				coordinate: r + l,
				value: i ? i[e] : e,
				index: t,
				offset: l
			} : null;
		}).filter(zt);
	}
}), Rx = B(Uy, _x, (e, t) => {
	if (!(e == null || t == null)) return wy(wy({}, e), {}, { scale: t });
});
B((e, t, n) => Hy(e, n), B([B([
	Uy,
	ex,
	$b,
	px
], gy)], Np), (e, t) => {
	if (!(e == null || t == null)) return wy(wy({}, e), {}, { scale: t });
});
var zx = B([
	Y,
	Ts,
	Es
], (e, t, n) => {
	switch (e) {
		case "horizontal": return t.some((e) => e.reversed) ? "right-to-left" : "left-to-right";
		case "vertical": return n.some((e) => e.reversed) ? "bottom-to-top" : "top-to-bottom";
		case "centric":
		case "radial": return "left-to-right";
		default: return;
	}
});
B([(e, t, n) => {
	var r;
	return (r = e.renderedTicks[t]) == null ? void 0 : r[n];
}], (e) => {
	if (!(!e || e.length === 0)) return (t) => {
		var n, r = Infinity, i = e[0];
		for (var a of e) {
			var o = Math.abs(a.coordinate - t);
			o < r && (r = o, i = a);
		}
		return (n = i) == null ? void 0 : n.value;
	};
});
//#endregion
//#region node_modules/recharts/es6/state/selectors/selectTooltipEventType.js
var Bx = (e) => e.options.defaultTooltipEventType, Vx = (e) => e.options.validateTooltipEventTypes;
function Hx(e, t, n) {
	if (e == null) return t;
	var r = e ? "axis" : "item";
	return n == null ? t : n.includes(r) ? r : t;
}
function Ux(e, t) {
	return Hx(t, Bx(e), Vx(e));
}
function Wx(e) {
	return z((t) => Ux(t, e));
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveLabel.js
var Gx = (e, t) => {
	var n, r = Number(t);
	if (!(Ot(r) || t == null)) return r >= 0 ? e == null || (n = e[r]) == null ? void 0 : n.value : void 0;
}, Kx = (e) => e.tooltip.settings, qx = {
	active: !1,
	index: null,
	dataKey: void 0,
	graphicalItemId: void 0,
	coordinate: void 0
}, Jx = eo({
	name: "tooltip",
	initialState: {
		itemInteraction: {
			click: qx,
			hover: qx
		},
		axisInteraction: {
			click: qx,
			hover: qx
		},
		keyboardInteraction: qx,
		syncInteraction: {
			active: !1,
			index: null,
			dataKey: void 0,
			label: void 0,
			coordinate: void 0,
			sourceViewBox: void 0,
			graphicalItemId: void 0
		},
		tooltipItemPayloads: [],
		settings: {
			shared: void 0,
			trigger: "hover",
			axisId: 0,
			active: !1,
			defaultIndex: void 0
		}
	},
	reducers: {
		addTooltipEntrySettings: {
			reducer(e, t) {
				e.tooltipItemPayloads.push(W(t.payload));
			},
			prepare: G()
		},
		replaceTooltipEntrySettings: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ea(e).tooltipItemPayloads.indexOf(W(r));
				a > -1 && (e.tooltipItemPayloads[a] = W(i));
			},
			prepare: G()
		},
		removeTooltipEntrySettings: {
			reducer(e, t) {
				var n = Ea(e).tooltipItemPayloads.indexOf(W(t.payload));
				n > -1 && e.tooltipItemPayloads.splice(n, 1);
			},
			prepare: G()
		},
		setTooltipSettingsState(e, t) {
			e.settings = t.payload;
		},
		setActiveMouseOverItemIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.keyboardInteraction.active = !1, e.itemInteraction.hover.active = !0, e.itemInteraction.hover.index = t.payload.activeIndex, e.itemInteraction.hover.dataKey = t.payload.activeDataKey, e.itemInteraction.hover.graphicalItemId = t.payload.activeGraphicalItemId, e.itemInteraction.hover.coordinate = t.payload.activeCoordinate;
		},
		mouseLeaveChart(e) {
			e.itemInteraction.hover.active = !1, e.axisInteraction.hover.active = !1;
		},
		mouseLeaveItem(e) {
			e.itemInteraction.hover.active = !1;
		},
		setActiveClickItemIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.itemInteraction.click.active = !0, e.keyboardInteraction.active = !1, e.itemInteraction.click.index = t.payload.activeIndex, e.itemInteraction.click.dataKey = t.payload.activeDataKey, e.itemInteraction.click.graphicalItemId = t.payload.activeGraphicalItemId, e.itemInteraction.click.coordinate = t.payload.activeCoordinate;
		},
		setMouseOverAxisIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.axisInteraction.hover.active = !0, e.keyboardInteraction.active = !1, e.axisInteraction.hover.index = t.payload.activeIndex, e.axisInteraction.hover.dataKey = t.payload.activeDataKey, e.axisInteraction.hover.coordinate = t.payload.activeCoordinate;
		},
		setMouseClickAxisIndex(e, t) {
			e.syncInteraction.active = !1, e.syncInteraction.sourceViewBox = void 0, e.keyboardInteraction.active = !1, e.axisInteraction.click.active = !0, e.axisInteraction.click.index = t.payload.activeIndex, e.axisInteraction.click.dataKey = t.payload.activeDataKey, e.axisInteraction.click.coordinate = t.payload.activeCoordinate;
		},
		setSyncInteraction(e, t) {
			e.syncInteraction = t.payload;
		},
		setKeyboardInteraction(e, t) {
			e.keyboardInteraction.active = t.payload.active, e.keyboardInteraction.index = t.payload.activeIndex, e.keyboardInteraction.coordinate = t.payload.activeCoordinate;
		}
	}
}), Yx = Jx.actions, Xx = Yx.addTooltipEntrySettings, Zx = Yx.replaceTooltipEntrySettings, Qx = Yx.removeTooltipEntrySettings, $x = Yx.setTooltipSettingsState, eS = Yx.setActiveMouseOverItemIndex, tS = Yx.mouseLeaveItem, nS = Yx.mouseLeaveChart, rS = Yx.setActiveClickItemIndex, iS = Yx.setMouseOverAxisIndex, aS = Yx.setMouseClickAxisIndex, oS = Yx.setSyncInteraction, sS = Yx.setKeyboardInteraction, cS = Jx.reducer;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipInteractionState.js
function lS(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function uS(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? lS(Object(n), !0).forEach(function(t) {
			dS(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : lS(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function dS(e, t, n) {
	return (t = fS(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function fS(e) {
	var t = pS(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function pS(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function mS(e, t, n) {
	return t === "axis" ? n === "click" ? e.axisInteraction.click : e.axisInteraction.hover : n === "click" ? e.itemInteraction.click : e.itemInteraction.hover;
}
function hS(e) {
	return e.index != null;
}
var gS = (e, t, n, r) => {
	if (t == null) return qx;
	var i = mS(e, t, n);
	if (i == null) return qx;
	if (i.active) return i;
	if (e.keyboardInteraction.active) return e.keyboardInteraction;
	if (e.syncInteraction.active && e.syncInteraction.index != null) return e.syncInteraction;
	var a = e.settings.active === !0;
	if (hS(i)) {
		if (a) return uS(uS({}, i), {}, { active: !0 });
	} else if (r != null) return {
		active: !0,
		coordinate: void 0,
		dataKey: void 0,
		index: r,
		graphicalItemId: void 0
	};
	return uS(uS({}, qx), {}, { coordinate: i.coordinate });
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineActiveTooltipIndex.js
function _S(e) {
	if (typeof e == "number") return Number.isFinite(e) ? e : void 0;
	if (e instanceof Date) {
		var t = e.valueOf();
		return Number.isFinite(t) ? t : void 0;
	}
	var n = Number(e);
	return Number.isFinite(n) ? n : void 0;
}
function vS(e, t) {
	var n = _S(e), r = t[0], i = t[1];
	return n !== void 0 && n >= Math.min(r, i) && n <= Math.max(r, i);
}
function yS(e, t, n) {
	if (n == null || t == null) return !0;
	var r = ns(e, t);
	return r == null || !Df(n) || vS(r, n);
}
var bS = (e, t, n, r) => {
	var i = e == null ? void 0 : e.index;
	if (i == null) return null;
	var a = Number(i);
	if (!q(a)) return i;
	var o = 0, s = Infinity;
	t.length > 0 && (s = t.length - 1);
	var c = Math.max(o, Math.min(a, s)), l = t[c];
	return l == null || yS(l, n, r) ? String(c) : null;
}, xS = (e, t, n, r, i, a, o) => {
	if (a != null) {
		var s = o[0], c = s == null ? void 0 : s.getPosition(a);
		if (c != null) return c;
		var l = i == null ? void 0 : i[Number(a)];
		if (l) switch (n) {
			case "horizontal": return {
				x: l.coordinate,
				y: (r.top + t) / 2
			};
			default: return {
				x: (r.left + e) / 2,
				y: l.coordinate
			};
		}
	}
}, SS = (e, t, n, r) => {
	if (t === "axis") return e.tooltipItemPayloads;
	if (e.tooltipItemPayloads.length === 0) return [];
	var i = n === "hover" ? e.itemInteraction.hover.graphicalItemId : e.itemInteraction.click.graphicalItemId;
	if (e.syncInteraction.active && i == null) return e.tooltipItemPayloads;
	if (i == null && (r != null || e.keyboardInteraction.active)) {
		var a = e.tooltipItemPayloads[0];
		return a == null ? [] : [a];
	}
	return e.tooltipItemPayloads.filter((e) => {
		var t;
		return ((t = e.settings) == null ? void 0 : t.graphicalItemId) === i;
	});
}, CS = (e) => e.options.tooltipPayloadSearcher, wS = (e) => e.tooltip;
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineTooltipPayload.js
function TS(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function ES(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? TS(Object(n), !0).forEach(function(t) {
			DS(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : TS(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function DS(e, t, n) {
	return (t = OS(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function OS(e) {
	var t = kS(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function kS(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function AS(e) {
	if (typeof e == "string" || typeof e == "number") return e;
}
function jS(e) {
	if (typeof e == "string" || typeof e == "number" || typeof e == "boolean") return e;
}
function MS(e) {
	if (typeof e == "string" || typeof e == "number") return e;
	if (typeof e == "function") return (t) => e(t);
}
function NS(e) {
	if (typeof e == "string") return e;
}
function PS(e) {
	if (!(typeof e != "object" || !e)) return {
		name: "name" in e ? AS(e.name) : void 0,
		unit: "unit" in e ? jS(e.unit) : void 0,
		dataKey: "dataKey" in e ? MS(e.dataKey) : void 0,
		payload: "payload" in e ? e.payload : void 0,
		color: "color" in e ? NS(e.color) : void 0,
		fill: "fill" in e ? NS(e.fill) : void 0
	};
}
function FS(e, t) {
	return e == null ? t : e;
}
var IS = (e, t, n, r, i, a, o) => {
	if (!(t == null || a == null)) {
		var s = n.chartData, c = n.computedData, l = n.dataStartIndex, u = n.dataEndIndex;
		return e.reduce((e, n) => {
			var d, f = n.dataDefinedOnItem, p = n.settings, m = FS(f, s), h = Array.isArray(m) ? Yo(m, l, u) : m, g = (d = p == null ? void 0 : p.dataKey) == null ? r : d, _ = p == null ? void 0 : p.nameKey, v = r && Array.isArray(h) && !Array.isArray(h[0]) && o === "axis" ? It(h, r, i) : a(h, t, c, _);
			if (Array.isArray(v)) v.forEach((t) => {
				var n, r, i = PS(t), a = i == null ? void 0 : i.name, o = i == null ? void 0 : i.dataKey, s = i == null ? void 0 : i.payload, c = ES(ES({}, p), {}, {
					name: a,
					unit: i == null ? void 0 : i.unit,
					color: (n = i == null ? void 0 : i.color) == null ? p == null ? void 0 : p.color : n,
					fill: (r = i == null ? void 0 : i.fill) == null ? p == null ? void 0 : p.fill : r
				});
				e.push(_s({
					tooltipEntrySettings: c,
					dataKey: o,
					payload: s,
					value: ns(s, o),
					name: a == null ? void 0 : String(a)
				}));
			});
			else {
				var y;
				e.push(_s({
					tooltipEntrySettings: p,
					dataKey: g,
					payload: v,
					value: ns(v, g),
					name: (y = ns(v, _)) == null ? p == null ? void 0 : p.name : y
				}));
			}
			return e;
		}, []);
	}
}, LS = B([
	gb,
	Ky,
	Qf
], yy), RS = B([
	B([(e) => e.graphicalItems.cartesianItems, (e) => e.graphicalItems.polarItems], (e, t) => [...e, ...t]),
	gb,
	B([jp, Mp], qy)
], Xy, { memoizeOptions: { resultEqualityCheck: kp } }), zS = B([RS], (e) => e.filter(Dp)), BS = B([RS], tb, { memoizeOptions: { resultEqualityCheck: kp } }), VS = B([RS], (e) => e.some((e) => !e.data)), HS = B([BS, hf], ib), US = B([
	zS,
	hf,
	gb
], Ep), WS = B([
	HS,
	gb,
	RS,
	hf,
	VS,
	BS
], sb), GS = B([gb], Cb), KS = B([GS, B([gb], (e) => e.allowDataOverflow)], kf), qS = B([
	B([
		US,
		B([RS], (e) => e.filter(Dp)),
		Xf,
		Zf
	], yb),
	hf,
	jp,
	KS
], xb), JS = B([
	HS,
	gb,
	B([RS], $y),
	Db,
	jp,
	bf
], Ab, { memoizeOptions: { resultEqualityCheck: Op } }), YS = B([B([
	Pb,
	jp,
	Mp
], Fb), jp], Vb), XS = B([B([
	Lb,
	jp,
	Mp
], Fb), jp], Ub), ZS = B([
	gb,
	Y,
	HS,
	WS,
	Xf,
	jp,
	B([
		gb,
		GS,
		KS,
		qS,
		JS,
		B([
			YS,
			B([B([
				zb,
				jp,
				Mp
			], Fb), jp], qb),
			XS
		], kb),
		Y,
		jp
	], Yb)
], Qb), QS = B([
	gb,
	ZS,
	B([
		ZS,
		gb,
		LS
	], tx),
	jp
], rx), $S = (e) => fx(e, jp(e), Mp(e), !1), eC = B([gb, $S], ap), tC = B([B([
	gb,
	LS,
	QS,
	eC
], gy)], Np), nC = B([
	Y,
	gb,
	LS,
	tC,
	$S,
	B([
		Y,
		WS,
		gb,
		jp
	], Px),
	B([
		Y,
		WS,
		gb,
		jp
	], hx),
	jp
], (e, t, n, r, i, a, o, s) => {
	if (t) {
		var c = t.type, l = is(e, s);
		if (r) {
			var u = n === "scaleBand" && r.bandwidth ? r.bandwidth() / 2 : 2, d = c === "category" && r.bandwidth ? r.bandwidth() / u : 0;
			return d = s === "angleAxis" && i != null && (i == null ? void 0 : i.length) >= 2 ? Dt(i[0] - i[1]) * 2 * d : d, l && o ? o.map((e, t) => {
				var n = r.map(e);
				return q(n) ? {
					coordinate: n + d,
					value: e,
					index: t,
					offset: d
				} : null;
			}).filter(zt) : r.domain().map((e, t) => {
				var n = r.map(e);
				return q(n) ? {
					coordinate: n + d,
					value: a ? a[e] : e,
					index: t,
					offset: d
				} : null;
			}).filter(zt);
		}
	}
}), rC = B([
	Bx,
	Vx,
	Kx
], (e, t, n) => Hx(n.shared, e, t)), iC = (e) => e.tooltip.settings.trigger, aC = (e) => e.tooltip.settings.defaultIndex, oC = B([
	wS,
	rC,
	iC,
	aC
], gS), sC = B([
	oC,
	HS,
	_b,
	ZS
], bS), cC = B([nC, sC], Gx), lC = B([oC], (e) => {
	if (e) return e.dataKey;
}), uC = B([oC], (e) => {
	if (e) return e.graphicalItemId;
}), dC = B([
	wS,
	rC,
	iC,
	aC
], SS), fC = B([oC, B([
	xs,
	Ss,
	Y,
	Rs,
	nC,
	aC,
	dC
], xS)], (e, t) => e != null && e.coordinate ? e.coordinate : t), pC = B([oC], (e) => {
	var t;
	return (t = e == null ? void 0 : e.active) != null && t;
});
B([B([
	dC,
	sC,
	hf,
	_b,
	cC,
	CS,
	rC
], IS)], (e) => {
	if (e != null) {
		var t = e.map((e) => e.payload).filter((e) => e != null);
		return Array.from(new Set(t));
	}
});
//#endregion
//#region node_modules/recharts/es6/context/useTooltipAxis.js
function mC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function hC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? mC(Object(n), !0).forEach(function(t) {
			gC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : mC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function gC(e, t, n) {
	return (t = _C(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function _C(e) {
	var t = vC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function vC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var yC = () => z(gb), bC = () => {
	var e = yC(), t = z(nC), n = z(tC);
	return gs(!e || !n ? void 0 : hC(hC({}, e), {}, { scale: n }), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getActiveCoordinate.js
function xC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function SC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? xC(Object(n), !0).forEach(function(t) {
			CC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : xC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function CC(e, t, n) {
	return (t = wC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function wC(e) {
	var t = TC(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function TC(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var EC = (e, t, n, r) => {
	var i = t.find((e) => e && e.index === n);
	if (i) {
		if (e === "horizontal") return {
			x: i.coordinate,
			y: r.relativeY
		};
		if (e === "vertical") return {
			x: r.relativeX,
			y: i.coordinate
		};
	}
	return {
		x: 0,
		y: 0
	};
}, DC = (e, t, n, r) => {
	var i = t.find((e) => e && e.index === n);
	if (i) {
		if (e === "centric") {
			var a = i.coordinate, o = r.radius;
			return SC(SC(SC({}, r), Vd(r.cx, r.cy, o, a)), {}, {
				angle: a,
				radius: o
			});
		}
		var s = i.coordinate, c = r.angle;
		return SC(SC(SC({}, r), Vd(r.cx, r.cy, s, c)), {}, {
			angle: c,
			radius: s
		});
	}
	return {
		angle: 0,
		clockWise: !1,
		cx: 0,
		cy: 0,
		endAngle: 0,
		innerRadius: 0,
		outerRadius: 0,
		radius: 0,
		startAngle: 0,
		x: 0,
		y: 0
	};
};
function OC(e, t) {
	var n = e.relativeX, r = e.relativeY;
	return n >= t.left && n <= t.left + t.width && r >= t.top && r <= t.top + t.height;
}
var kC = (e, t, n, r, i) => {
	var a, o = (a = t == null ? void 0 : t.length) == null ? 0 : a;
	if (o <= 1 || e == null) return 0;
	if (r === "angleAxis" && i != null && Math.abs(Math.abs(i[1] - i[0]) - 360) <= 1e-6) for (var s = 0; s < o; s++) {
		var c, l, u, d, f, p = s > 0 ? (c = n[s - 1]) == null ? void 0 : c.coordinate : (l = n[o - 1]) == null ? void 0 : l.coordinate, m = (u = n[s]) == null ? void 0 : u.coordinate, h = s >= o - 1 ? (d = n[0]) == null ? void 0 : d.coordinate : (f = n[s + 1]) == null ? void 0 : f.coordinate, g = void 0;
		if (!(p == null || m == null || h == null)) if (Dt(m - p) !== Dt(h - m)) {
			var _ = [];
			if (Dt(h - m) === Dt(i[1] - i[0])) {
				g = h;
				var v = m + i[1] - i[0];
				_[0] = Math.min(v, (v + p) / 2), _[1] = Math.max(v, (v + p) / 2);
			} else {
				g = p;
				var y = h + i[1] - i[0];
				_[0] = Math.min(m, (y + m) / 2), _[1] = Math.max(m, (y + m) / 2);
			}
			var b = [Math.min(m, (g + m) / 2), Math.max(m, (g + m) / 2)];
			if (e > b[0] && e <= b[1] || e >= _[0] && e <= _[1]) {
				var x;
				return (x = n[s]) == null ? void 0 : x.index;
			}
		} else {
			var S = Math.min(p, h), C = Math.max(p, h);
			if (e > (S + m) / 2 && e <= (C + m) / 2) {
				var w;
				return (w = n[s]) == null ? void 0 : w.index;
			}
		}
	}
	else if (t) for (var T = 0; T < o; T++) {
		var E = t[T];
		if (E != null) {
			var D = t[T + 1], O = t[T - 1];
			if (T === 0 && D != null && e <= (E.coordinate + D.coordinate) / 2 || T === o - 1 && O != null && e > (E.coordinate + O.coordinate) / 2 || T > 0 && T < o - 1 && O != null && D != null && e > (E.coordinate + O.coordinate) / 2 && e <= (E.coordinate + D.coordinate) / 2) return E.index;
		}
	}
	return -1;
}, AC = () => z(Qf), jC = (e, t) => t, MC = (e, t, n) => n, NC = (e, t, n, r) => r, PC = B(nC, (e) => Br(e, (e) => e.coordinate)), FC = B([
	wS,
	jC,
	MC,
	NC
], gS), IC = B([
	FC,
	HS,
	_b,
	ZS
], bS), LC = (e, t, n) => {
	if (t != null) {
		var r = wS(e);
		return t === "axis" ? n === "hover" ? r.axisInteraction.hover.dataKey : r.axisInteraction.click.dataKey : n === "hover" ? r.itemInteraction.hover.dataKey : r.itemInteraction.click.dataKey;
	}
}, RC = B([
	wS,
	jC,
	MC,
	NC
], SS), zC = B([
	xs,
	Ss,
	Y,
	Rs,
	nC,
	NC,
	RC
], xS), BC = B([FC, zC], (e, t) => {
	var n;
	return (n = e.coordinate) == null ? t : n;
}), VC = B([nC, IC], Gx), HC = B([
	RC,
	IC,
	hf,
	_b,
	VC,
	CS,
	jC
], IS), UC = B([FC, IC], (e, t) => ({
	isActive: e.active && t != null,
	activeIndex: t
})), WC = (e, t, n, r, i, a, o) => {
	if (!(!e || !n || !r || !i) && OC(e, o)) {
		var s = kC(ys(e, t), a, i, n, r), c = EC(t, i, s, e);
		return {
			activeIndex: String(s),
			activeCoordinate: c
		};
	}
}, GC = (e, t, n, r, i, a, o) => {
	if (!(!e || !r || !i || !a || !n)) {
		var s = qd(e, n);
		if (s) {
			var c = kC(bs(s, t), o, a, r, i), l = DC(t, a, c, s);
			return {
				activeIndex: String(c),
				activeCoordinate: l
			};
		}
	}
}, KC = (e, t, n, r, i, a, o, s) => {
	if (!(!e || !t || !r || !i || !a)) return t === "horizontal" || t === "vertical" ? WC(e, t, r, i, a, o, s) : GC(e, t, n, r, i, a, o);
}, qC = B((e) => e.zIndex.zIndexMap, (e, t) => t, (e, t, n) => n, (e, t, n) => {
	if (t != null) {
		var r = e[t];
		if (r != null) return n ? r.panoramaElement : r.element;
	}
}), JC = B((e) => e.zIndex.zIndexMap, (e) => {
	var t = Object.keys(e).map((e) => parseInt(e, 10)).concat(Object.values(np));
	return Array.from(new Set(t)).sort((e, t) => e - t);
}, { memoizeOptions: { resultEqualityCheck: Ap } });
//#endregion
//#region node_modules/recharts/es6/state/zIndexSlice.js
function YC(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function XC(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? YC(Object(n), !0).forEach(function(t) {
			ZC(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : YC(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function ZC(e, t, n) {
	return (t = QC(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function QC(e) {
	var t = $C(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function $C(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var ew = { zIndexMap: Object.values(np).reduce((e, t) => XC(XC({}, e), {}, { [t]: {
	element: void 0,
	panoramaElement: void 0,
	consumers: 0
} }), {}) }, tw = new Set(Object.values(np));
function nw(e) {
	return tw.has(e);
}
var rw = eo({
	name: "zIndex",
	initialState: ew,
	reducers: {
		registerZIndexPortal: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] ? e.zIndexMap[n].consumers += 1 : e.zIndexMap[n] = {
					consumers: 1,
					element: void 0,
					panoramaElement: void 0
				};
			},
			prepare: G()
		},
		unregisterZIndexPortal: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (--e.zIndexMap[n].consumers, e.zIndexMap[n].consumers <= 0 && !nw(n) && delete e.zIndexMap[n]);
			},
			prepare: G()
		},
		registerZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload, r = n.zIndex, i = n.element, a = n.isPanorama;
				e.zIndexMap[r] ? a ? e.zIndexMap[r].panoramaElement = W(i) : e.zIndexMap[r].element = W(i) : e.zIndexMap[r] = {
					consumers: 0,
					element: a ? void 0 : W(i),
					panoramaElement: a ? W(i) : void 0
				};
			},
			prepare: G()
		},
		unregisterZIndexPortalElement: {
			reducer: (e, t) => {
				var n = t.payload.zIndex;
				e.zIndexMap[n] && (t.payload.isPanorama ? e.zIndexMap[n].panoramaElement = void 0 : e.zIndexMap[n].element = void 0);
			},
			prepare: G()
		}
	}
}), iw = rw.actions, aw = iw.registerZIndexPortal, ow = iw.unregisterZIndexPortal, sw = iw.registerZIndexPortalElement, cw = iw.unregisterZIndexPortalElement, lw = rw.reducer, uw = h();
function dw(e) {
	var t = e.zIndex, n = e.children, r = Mc() && t !== void 0 && t !== 0, i = Hs(), a = (0, C.useRef)(void 0), o = (0, C.useRef)(/* @__PURE__ */ new Set()), s = R(), c = z((e) => qC(e, t, i));
	if ((0, C.useLayoutEffect)(() => {
		if (!r) {
			var e = o.current;
			e.forEach((e) => {
				s(ow({ zIndex: e }));
			}), e.clear(), a.current = void 0;
			return;
		}
		if (o.current.has(t) || (s(aw({ zIndex: t })), o.current.add(t)), c) {
			a.current = c;
			var n = o.current;
			n.forEach((e) => {
				e !== t && (s(ow({ zIndex: e })), n.delete(e));
			});
		}
	}, [
		s,
		t,
		r,
		c
	]), (0, C.useLayoutEffect)(() => {
		var e = o.current;
		return () => {
			e.forEach((e) => {
				s(ow({ zIndex: e }));
			}), e.clear();
		};
	}, [s]), !r) return n;
	var l = c == null ? a.current : c;
	return l ? /*#__PURE__*/ (0, uw.createPortal)(n, l) : null;
}
//#endregion
//#region node_modules/recharts/es6/component/Cursor.js
function fw() {
	return fw = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, fw.apply(null, arguments);
}
function pw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function mw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? pw(Object(n), !0).forEach(function(t) {
			hw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : pw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function hw(e, t, n) {
	return (t = gw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function gw(e) {
	var t = _w(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function _w(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function vw(e) {
	var t = e.cursor, n = e.cursorComp, r = e.cursorProps;
	return /*#__PURE__*/ (0, C.isValidElement)(t) ? /*#__PURE__*/ (0, C.cloneElement)(t, r) : /*#__PURE__*/ (0, C.createElement)(n, r);
}
function yw(e) {
	var t, n = e.coordinate, r = e.payload, i = e.index, a = e.offset, o = e.tooltipAxisBandSize, s = e.layout, c = e.cursor, l = e.tooltipEventType, u = e.chartName, d = n, f = r, p = i;
	if (!c || !d || u !== "ScatterChart" && l !== "axis") return null;
	var m, h, g;
	if (u === "ScatterChart") m = d, h = bu, g = np.cursorLine;
	else if (u === "BarChart") m = xu(s, d, a, o), h = Nd, g = np.cursorRectangle;
	else if (s === "radial" && Vt(d)) {
		var _ = Jd(d), v = _.cx, y = _.cy, b = _.radius;
		m = {
			cx: v,
			cy: y,
			startAngle: _.startAngle,
			endAngle: _.endAngle,
			innerRadius: b,
			outerRadius: b
		}, h = uf, g = np.cursorLine;
	} else m = { points: df(s, d, a) }, h = lu, g = np.cursorLine;
	var x = typeof c == "object" && "className" in c ? c.className : void 0, S = mw(mw(mw(mw({
		stroke: "#ccc",
		pointerEvents: "none"
	}, a), m), ie(c)), {}, {
		payload: f,
		payloadIndex: p,
		className: N("recharts-tooltip-cursor", x)
	});
	return /*#__PURE__*/ C.createElement(dw, { zIndex: (t = e.zIndex) == null ? g : t }, /*#__PURE__*/ C.createElement(vw, {
		cursor: c,
		cursorComp: h,
		cursorProps: S
	}));
}
function bw(e) {
	var t = bC(), n = Ec(), r = kc(), i = AC();
	return t == null || n == null || r == null || i == null ? null : /*#__PURE__*/ C.createElement(yw, fw({}, e, {
		offset: n,
		layout: r,
		tooltipAxisBandSize: t,
		chartName: i
	}));
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipPortalContext.js
var xw = /*#__PURE__*/ (0, C.createContext)(null), Sw = () => (0, C.useContext)(xw), Cw = (/* @__PURE__ */ l((/* @__PURE__ */ o(((e, t) => {
	var n = Object.prototype.hasOwnProperty, r = "~";
	function i() {}
	Object.create && (i.prototype = Object.create(null), new i().__proto__ || (r = !1));
	function a(e, t, n) {
		this.fn = e, this.context = t, this.once = n || !1;
	}
	function o(e, t, n, i, o) {
		if (typeof n != "function") throw TypeError("The listener must be a function");
		var s = new a(n, i || e, o), c = r ? r + t : t;
		return e._events[c] ? e._events[c].fn ? e._events[c] = [e._events[c], s] : e._events[c].push(s) : (e._events[c] = s, e._eventsCount++), e;
	}
	function s(e, t) {
		--e._eventsCount === 0 ? e._events = new i() : delete e._events[t];
	}
	function c() {
		this._events = new i(), this._eventsCount = 0;
	}
	c.prototype.eventNames = function() {
		var e = [], t, i;
		if (this._eventsCount === 0) return e;
		for (i in t = this._events) n.call(t, i) && e.push(r ? i.slice(1) : i);
		return Object.getOwnPropertySymbols ? e.concat(Object.getOwnPropertySymbols(t)) : e;
	}, c.prototype.listeners = function(e) {
		var t = r ? r + e : e, n = this._events[t];
		if (!n) return [];
		if (n.fn) return [n.fn];
		for (var i = 0, a = n.length, o = Array(a); i < a; i++) o[i] = n[i].fn;
		return o;
	}, c.prototype.listenerCount = function(e) {
		var t = r ? r + e : e, n = this._events[t];
		return n ? n.fn ? 1 : n.length : 0;
	}, c.prototype.emit = function(e, t, n, i, a, o) {
		var s = r ? r + e : e;
		if (!this._events[s]) return !1;
		var c = this._events[s], l = arguments.length, u, d;
		if (c.fn) {
			switch (c.once && this.removeListener(e, c.fn, void 0, !0), l) {
				case 1: return c.fn.call(c.context), !0;
				case 2: return c.fn.call(c.context, t), !0;
				case 3: return c.fn.call(c.context, t, n), !0;
				case 4: return c.fn.call(c.context, t, n, i), !0;
				case 5: return c.fn.call(c.context, t, n, i, a), !0;
				case 6: return c.fn.call(c.context, t, n, i, a, o), !0;
			}
			for (d = 1, u = Array(l - 1); d < l; d++) u[d - 1] = arguments[d];
			c.fn.apply(c.context, u);
		} else {
			var f = c.length, p;
			for (d = 0; d < f; d++) switch (c[d].once && this.removeListener(e, c[d].fn, void 0, !0), l) {
				case 1:
					c[d].fn.call(c[d].context);
					break;
				case 2:
					c[d].fn.call(c[d].context, t);
					break;
				case 3:
					c[d].fn.call(c[d].context, t, n);
					break;
				case 4:
					c[d].fn.call(c[d].context, t, n, i);
					break;
				default:
					if (!u) for (p = 1, u = Array(l - 1); p < l; p++) u[p - 1] = arguments[p];
					c[d].fn.apply(c[d].context, u);
			}
		}
		return !0;
	}, c.prototype.on = function(e, t, n) {
		return o(this, e, t, n, !1);
	}, c.prototype.once = function(e, t, n) {
		return o(this, e, t, n, !0);
	}, c.prototype.removeListener = function(e, t, n, i) {
		var a = r ? r + e : e;
		if (!this._events[a]) return this;
		if (!t) return s(this, a), this;
		var o = this._events[a];
		if (o.fn) o.fn === t && (!i || o.once) && (!n || o.context === n) && s(this, a);
		else {
			for (var c = 0, l = [], u = o.length; c < u; c++) (o[c].fn !== t || i && !o[c].once || n && o[c].context !== n) && l.push(o[c]);
			l.length ? this._events[a] = l.length === 1 ? l[0] : l : s(this, a);
		}
		return this;
	}, c.prototype.removeAllListeners = function(e) {
		var t;
		return e ? (t = r ? r + e : e, this._events[t] && s(this, t)) : (this._events = new i(), this._eventsCount = 0), this;
	}, c.prototype.off = c.prototype.removeListener, c.prototype.addListener = c.prototype.on, c.prefixed = r, c.EventEmitter = c, t !== void 0 && (t.exports = c);
})))(), 1)).default, ww = new Cw(), Tw = "recharts.syncEvent.tooltip", Ew = "recharts.syncEvent.brush", Dw = (e, t) => {
	if (t && Array.isArray(e)) {
		var n = Number.parseInt(t, 10);
		if (!Ot(n)) return e[n];
	}
}, Ow = eo({
	name: "options",
	initialState: {
		chartName: "",
		tooltipPayloadSearcher: () => void 0,
		eventEmitter: void 0,
		defaultTooltipEventType: "axis"
	},
	reducers: { createEventEmitter: (e) => {
		e.eventEmitter == null && (e.eventEmitter = Symbol("rechartsEventEmitter"));
	} }
}), kw = Ow.reducer, Aw = Ow.actions.createEventEmitter;
//#endregion
//#region node_modules/recharts/es6/synchronisation/syncSelectors.js
function jw(e) {
	return e.tooltip.syncInteraction;
}
var Mw = eo({
	name: "chartData",
	initialState: {
		chartData: void 0,
		computedData: void 0,
		dataStartIndex: 0,
		dataEndIndex: 0
	},
	reducers: {
		setChartData(e, t) {
			if (e.chartData = W(t.payload), t.payload == null) {
				e.dataStartIndex = 0, e.dataEndIndex = 0;
				return;
			}
			t.payload.length > 0 && e.dataEndIndex !== t.payload.length - 1 && (e.dataEndIndex = t.payload.length - 1);
		},
		setComputedData(e, t) {
			e.computedData = t.payload;
		},
		setDataStartEndIndexes(e, t) {
			var n = t.payload, r = n.startIndex, i = n.endIndex;
			r != null && (e.dataStartIndex = r), i != null && (e.dataEndIndex = i);
		}
	}
}), Nw = Mw.actions, Pw = Nw.setChartData, Fw = Nw.setDataStartEndIndexes;
Nw.setComputedData;
var Iw = Mw.reducer, Lw = ["x", "y"];
function Rw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function zw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Rw(Object(n), !0).forEach(function(t) {
			Bw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Rw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Bw(e, t, n) {
	return (t = Vw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Vw(e) {
	var t = Hw(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function Hw(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Uw(e, t) {
	if (e == null) return {};
	var n, r, i = Ww(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Ww(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function Gw() {
	var e = z($f), t = z(tp), n = R(), r = z(ep), i = z(nC), a = kc(), o = wc();
	(0, C.useEffect)(() => {
		if (e == null) return Bt;
		var s = (s, c, l) => {
			if (t !== l && e === s) {
				if (c.payload.active === !1) {
					n(oS({
						active: !1,
						coordinate: void 0,
						dataKey: void 0,
						index: null,
						label: void 0,
						sourceViewBox: void 0,
						graphicalItemId: void 0
					}));
					return;
				}
				if (r === "index") {
					var u;
					if (o && c != null && (u = c.payload) != null && u.coordinate && c.payload.sourceViewBox) {
						var d = c.payload.coordinate, f = d.x, p = d.y, m = Uw(d, Lw), h = c.payload.sourceViewBox, g = h.x, _ = h.y, v = h.width, y = h.height, b = zw(zw({}, m), {}, {
							x: o.x + (v ? (f - g) / v : 0) * o.width,
							y: o.y + (y ? (p - _) / y : 0) * o.height
						});
						n(zw(zw({}, c), {}, { payload: zw(zw({}, c.payload), {}, { coordinate: b }) }));
					} else n(c);
					return;
				}
				if (i != null) {
					var x;
					typeof r == "function" ? x = i[r(i, {
						activeTooltipIndex: c.payload.index == null ? void 0 : Number(c.payload.index),
						isTooltipActive: c.payload.active,
						activeIndex: c.payload.index == null ? void 0 : Number(c.payload.index),
						activeLabel: c.payload.label,
						activeDataKey: c.payload.dataKey,
						activeCoordinate: c.payload.coordinate
					})] : r === "value" && (x = i.find((e) => String(e.value) === c.payload.label));
					var S = c.payload.coordinate;
					if (S == null || o == null) {
						n(oS({
							active: !1,
							coordinate: void 0,
							dataKey: void 0,
							index: null,
							label: void 0,
							sourceViewBox: void 0,
							graphicalItemId: void 0
						}));
						return;
					}
					if (x == null) {
						n(oS({
							active: !1,
							coordinate: void 0,
							dataKey: void 0,
							index: null,
							label: void 0,
							sourceViewBox: c.payload.sourceViewBox,
							graphicalItemId: void 0
						}));
						return;
					}
					var C = S.x, w = S.y, T = Math.min(C, o.x + o.width), E = Math.min(w, o.y + o.height), D = {
						x: a === "horizontal" ? x.coordinate : T,
						y: a === "horizontal" ? E : x.coordinate
					};
					n(oS({
						active: c.payload.active,
						coordinate: D,
						dataKey: c.payload.dataKey,
						index: String(x.index),
						label: c.payload.label,
						sourceViewBox: c.payload.sourceViewBox,
						graphicalItemId: c.payload.graphicalItemId
					}));
				}
			}
		};
		return ww.on(Tw, s), () => {
			ww.off(Tw, s);
		};
	}, [
		z((e) => e.rootProps.className),
		n,
		t,
		e,
		r,
		i,
		a,
		o
	]);
}
function Kw() {
	var e = z($f), t = z(tp), n = R();
	(0, C.useEffect)(() => {
		if (e == null) return Bt;
		var r = (r, i, a) => {
			t !== a && e === r && n(Fw(i));
		};
		return ww.on(Ew, r), () => {
			ww.off(Ew, r);
		};
	}, [
		n,
		t,
		e
	]);
}
function qw() {
	var e = R();
	(0, C.useEffect)(() => {
		e(Aw());
	}, [e]), Gw(), Kw();
}
function Jw(e, t, n, r, i, a) {
	var o = z((n) => LC(n, e, t)), s = z(uC), c = z(tp), l = z($f), u = z(ep), d = z(jw), f = (d == null ? void 0 : d.sourceViewBox) != null, p = wc();
	(0, C.useEffect)(() => {
		if (!f && l != null && c != null) {
			var e = oS({
				active: a,
				coordinate: n,
				dataKey: o,
				index: i,
				label: typeof r == "number" ? String(r) : r,
				sourceViewBox: p,
				graphicalItemId: s
			});
			ww.emit(Tw, l, e, c);
		}
	}, [
		f,
		n,
		o,
		s,
		i,
		r,
		c,
		l,
		u,
		a,
		p
	]);
}
//#endregion
//#region node_modules/recharts/es6/component/Tooltip.js
function Yw(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Xw(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Yw(Object(n), !0).forEach(function(t) {
			Zw(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Yw(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Zw(e, t, n) {
	return (t = Qw(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Qw(e) {
	var t = $w(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function $w(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function eT(e, t) {
	return aT(e) || iT(e, t) || nT(e, t) || tT();
}
function tT() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function nT(e, t) {
	if (e) {
		if (typeof e == "string") return rT(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? rT(e, t) : void 0;
	}
}
function rT(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function iT(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function aT(e) {
	if (Array.isArray(e)) return e;
}
function oT(e) {
	return e.dataKey;
}
function sT(e, t) {
	return /*#__PURE__*/ C.isValidElement(e) ? /*#__PURE__*/ C.cloneElement(e, t) : typeof e == "function" ? /*#__PURE__*/ C.createElement(e, t) : /*#__PURE__*/ C.createElement(yl, t);
}
var cT = [], lT = {
	allowEscapeViewBox: {
		x: !1,
		y: !1
	},
	animationDuration: 400,
	animationEasing: "ease",
	axisId: 0,
	contentStyle: {},
	cursor: !0,
	filterNull: !0,
	includeHidden: !1,
	isAnimationActive: "auto",
	itemSorter: "name",
	itemStyle: {},
	labelStyle: {},
	offset: 10,
	reverseDirection: {
		x: !1,
		y: !1
	},
	separator: " : ",
	trigger: "hover",
	useTranslate3d: !1,
	wrapperStyle: {}
};
function uT(e) {
	var t, n, r = Yt(e, lT), i = r.active, a = r.allowEscapeViewBox, o = r.animationDuration, s = r.animationEasing, c = r.content, l = r.filterNull, u = r.isAnimationActive, d = r.offset, f = r.payloadUniqBy, p = r.position, m = r.reverseDirection, h = r.useTranslate3d, g = r.wrapperStyle, _ = r.cursor, v = r.shared, y = r.trigger, b = r.defaultIndex, x = r.portal, S = r.axisId, w = R(), T = typeof b == "number" ? String(b) : b;
	(0, C.useEffect)(() => {
		w($x({
			shared: v,
			trigger: y,
			axisId: S,
			active: i,
			defaultIndex: T
		}));
	}, [
		w,
		v,
		y,
		S,
		i,
		T
	]);
	var E = wc(), D = Jl(), O = Wx(v), k = (t = z((e) => UC(e, O, y, T))) == null ? {} : t, A = k.activeIndex, j = k.isActive, M = z((e) => HC(e, O, y, T)), N = z((e) => VC(e, O, y, T)), P = z((e) => BC(e, O, y, T)), ee = M, te = Sw(), ne = (n = i == null ? j : i) != null && n, re = eT(Qr([ee, ne]), 2), F = re[0], ie = re[1], ae = O === "axis" ? N : void 0;
	Jw(O, y, P, ae, A, ne);
	var oe = x == null ? te : x;
	if (oe == null || E == null || O == null) return null;
	var se = ee == null ? cT : ee;
	ne || (se = cT), l && se.length && (se = rr(se.filter((e) => e.value != null && (e.hide !== !0 || r.includeHidden)), f, oT));
	var ce = se.length > 0, le = Xw(Xw({}, r), {}, {
		payload: se,
		label: ae,
		active: ne,
		activeIndex: A,
		coordinate: P,
		accessibilityLayer: D
	}), ue = /*#__PURE__*/ C.createElement(ql, {
		allowEscapeViewBox: a,
		animationDuration: o,
		animationEasing: s,
		isAnimationActive: u,
		active: ne,
		coordinate: P,
		hasPayload: ce,
		offset: d,
		position: p,
		reverseDirection: m,
		useTranslate3d: h,
		viewBox: E,
		wrapperStyle: g,
		lastBoundingBox: F,
		innerRef: ie,
		hasPortalFromProps: !!x
	}, sT(c, le));
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ (0, uw.createPortal)(ue, oe), ne && /*#__PURE__*/ C.createElement(bw, {
		cursor: _,
		tooltipEventType: O,
		coordinate: P,
		payload: se,
		index: A
	}));
}
//#endregion
//#region node_modules/recharts/es6/component/Cell.js
var dT = (e) => null;
dT.displayName = "Cell";
//#endregion
//#region node_modules/recharts/es6/util/LRUCache.js
function fT(e, t, n) {
	return (t = pT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function pT(e) {
	var t = mT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function mT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var hT = class {
	constructor(e) {
		fT(this, "cache", /* @__PURE__ */ new Map()), this.maxSize = e;
	}
	get(e) {
		var t = this.cache.get(e);
		return t !== void 0 && (this.cache.delete(e), this.cache.set(e, t)), t;
	}
	set(e, t) {
		if (this.cache.has(e)) this.cache.delete(e);
		else if (this.cache.size >= this.maxSize) {
			var n = this.cache.keys().next().value;
			n != null && this.cache.delete(n);
		}
		this.cache.set(e, t);
	}
	clear() {
		this.cache.clear();
	}
	size() {
		return this.cache.size;
	}
};
//#endregion
//#region node_modules/recharts/es6/util/DOMUtils.js
function gT(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function _T(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? gT(Object(n), !0).forEach(function(t) {
			vT(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : gT(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function vT(e, t, n) {
	return (t = yT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function yT(e) {
	var t = bT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function bT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var xT = _T({}, {
	cacheSize: 2e3,
	enableCache: !0
}), ST = new hT(xT.cacheSize), CT = {
	position: "absolute",
	top: "-20000px",
	left: 0,
	padding: 0,
	margin: 0,
	border: "none",
	whiteSpace: "pre"
}, wT = "recharts_measurement_span";
function TT(e, t) {
	return `${e}|${t.fontSize || ""}|${t.fontFamily || ""}|${t.fontWeight || ""}|${t.fontStyle || ""}|${t.letterSpacing || ""}|${t.textTransform || ""}`;
}
var ET = (e, t) => {
	try {
		var n = document.getElementById(wT);
		n || (n = document.createElement("span"), n.setAttribute("id", wT), n.setAttribute("aria-hidden", "true"), document.body.appendChild(n)), Object.assign(n.style, CT, t), n.textContent = `${e}`;
		var r = n.getBoundingClientRect();
		return {
			width: r.width,
			height: r.height
		};
	} catch (e) {
		return {
			width: 0,
			height: 0
		};
	}
}, DT = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : {};
	if (e == null || El.isSsr) return {
		width: 0,
		height: 0
	};
	if (!xT.enableCache) return ET(e, t);
	var n = TT(e, t), r = ST.get(n);
	if (r) return r;
	var i = ET(e, t);
	return ST.set(n, i), i;
}, OT;
function kT(e, t) {
	return PT(e) || NT(e, t) || jT(e, t) || AT();
}
function AT() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function jT(e, t) {
	if (e) {
		if (typeof e == "string") return MT(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? MT(e, t) : void 0;
	}
}
function MT(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function NT(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function PT(e) {
	if (Array.isArray(e)) return e;
}
function FT(e, t, n) {
	return (t = IT(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function IT(e) {
	var t = LT(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function LT(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var RT = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([*/])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, zT = /(-?\d+(?:\.\d+)?[a-zA-Z%]*)([+-])(-?\d+(?:\.\d+)?[a-zA-Z%]*)/, BT = /^(px|cm|vh|vw|em|rem|%|mm|in|pt|pc|ex|ch|vmin|vmax|Q)$/, VT = /(-?\d+(?:\.\d+)?)([a-zA-Z%]+)?/, HT = {
	cm: 96 / 2.54,
	mm: 96 / 25.4,
	pt: 96 / 72,
	pc: 96 / 6,
	in: 96,
	Q: 96 / (2.54 * 40),
	px: 1
}, UT = [
	"cm",
	"mm",
	"pt",
	"pc",
	"in",
	"Q",
	"px"
];
function WT(e) {
	return UT.includes(e);
}
var GT = "NaN";
function KT(e, t) {
	return e * HT[t];
}
var qT = class e {
	static parse(t) {
		var n, r = kT((n = VT.exec(t)) == null ? [] : n, 3), i = r[1], a = r[2];
		return i == null ? e.NaN : new e(parseFloat(i), a == null ? "" : a);
	}
	constructor(e, t) {
		this.num = e, this.unit = t, this.num = e, this.unit = t, Ot(e) && (this.unit = ""), t !== "" && !BT.test(t) && (this.num = NaN, this.unit = ""), WT(t) && (this.num = KT(e, t), this.unit = "px");
	}
	add(t) {
		return this.unit === t.unit ? new e(this.num + t.num, this.unit) : new e(NaN, "");
	}
	subtract(t) {
		return this.unit === t.unit ? new e(this.num - t.num, this.unit) : new e(NaN, "");
	}
	multiply(t) {
		return this.unit !== "" && t.unit !== "" && this.unit !== t.unit ? new e(NaN, "") : new e(this.num * t.num, this.unit || t.unit);
	}
	divide(t) {
		return this.unit !== "" && t.unit !== "" && this.unit !== t.unit ? new e(NaN, "") : new e(this.num / t.num, this.unit || t.unit);
	}
	toString() {
		return `${this.num}${this.unit}`;
	}
	isNaN() {
		return Ot(this.num);
	}
};
OT = qT, FT(qT, "NaN", new OT(NaN, ""));
function JT(e) {
	if (e == null || e.includes(GT)) return GT;
	for (var t = e; t.includes("*") || t.includes("/");) {
		var n, r = kT((n = RT.exec(t)) == null ? [] : n, 4), i = r[1], a = r[2], o = r[3], s = qT.parse(i == null ? "" : i), c = qT.parse(o == null ? "" : o), l = a === "*" ? s.multiply(c) : s.divide(c);
		if (l.isNaN()) return GT;
		t = t.replace(RT, l.toString());
	}
	for (; t.includes("+") || /.-\d+(?:\.\d+)?/.test(t);) {
		var u, d = kT((u = zT.exec(t)) == null ? [] : u, 4), f = d[1], p = d[2], m = d[3], h = qT.parse(f == null ? "" : f), g = qT.parse(m == null ? "" : m), _ = p === "+" ? h.add(g) : h.subtract(g);
		if (_.isNaN()) return GT;
		t = t.replace(zT, _.toString());
	}
	return t;
}
var YT = /\(([^()]*)\)/;
function XT(e) {
	for (var t = e, n; (n = YT.exec(t)) != null;) {
		var r = kT(n, 2)[1];
		t = t.replace(YT, JT(r));
	}
	return t;
}
function ZT(e) {
	var t = e.replace(/\s+/g, "");
	return t = XT(t), t = JT(t), t;
}
function QT(e) {
	try {
		return ZT(e);
	} catch (e) {
		return GT;
	}
}
function $T(e) {
	var t = QT(e.slice(5, -1));
	return t === GT ? "" : t;
}
//#endregion
//#region node_modules/recharts/es6/component/Text.js
var eE = [
	"x",
	"y",
	"lineHeight",
	"capHeight",
	"fill",
	"scaleToFit",
	"textAnchor",
	"verticalAnchor"
], tE = [
	"dx",
	"dy",
	"angle",
	"className",
	"breakAll"
];
function nE() {
	return nE = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, nE.apply(null, arguments);
}
function rE(e, t) {
	if (e == null) return {};
	var n, r, i = iE(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function iE(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function aE(e, t) {
	return uE(e) || lE(e, t) || sE(e, t) || oE();
}
function oE() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function sE(e, t) {
	if (e) {
		if (typeof e == "string") return cE(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? cE(e, t) : void 0;
	}
}
function cE(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function lE(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function uE(e) {
	if (Array.isArray(e)) return e;
}
var dE = /[ \f\n\r\t\v\u2028\u2029]+/, fE = (e) => {
	var t = e.children, n = e.breakAll, r = e.style;
	try {
		var i = [];
		return Lt(t) || (i = n ? t.toString().split("") : t.toString().split(dE)), {
			wordsWithComputedWidth: i.map((e) => ({
				word: e,
				width: DT(e, r).width
			})),
			spaceWidth: n ? 0 : DT("\xA0", r).width
		};
	} catch (e) {
		return null;
	}
};
function pE(e) {
	return e === "start" || e === "middle" || e === "end" || e === "inherit";
}
function mE(e) {
	return Lt(e) || typeof e == "string" || typeof e == "number" || typeof e == "boolean";
}
var hE = (e, t, n, r) => e.reduce((e, i) => {
	var a = i.word, o = i.width, s = e[e.length - 1];
	if (s && o != null && (t == null || r || s.width + o + n < Number(t))) s.words.push(a), s.width += o + n;
	else {
		var c = {
			words: [a],
			width: o
		};
		e.push(c);
	}
	return e;
}, []), gE = (e) => e.reduce((e, t) => e.width > t.width ? e : t), _E = "…", vE = (e, t, n, r, i, a, o, s) => {
	var c = fE({
		breakAll: n,
		style: r,
		children: e.slice(0, t) + _E
	});
	if (!c) return [!1, []];
	var l = hE(c.wordsWithComputedWidth, a, o, s);
	return [l.length > i || gE(l).width > Number(a), l];
}, yE = (e, t, n, r, i) => {
	var a = e.maxLines, o = e.children, s = e.style, c = e.breakAll, l = I(a), u = String(o), d = hE(t, r, n, i);
	if (!l || i || !(d.length > a || gE(d).width > Number(r))) return d;
	for (var f = 0, p = u.length - 1, m = 0, h; f <= p && m <= u.length - 1;) {
		var g = Math.floor((f + p) / 2), _ = aE(vE(u, g - 1, c, s, a, r, n, i), 2), v = _[0], y = _[1], b = aE(vE(u, g, c, s, a, r, n, i), 1)[0];
		if (!v && !b && (f = g + 1), v && b && (p = g - 1), !v && b) {
			h = y;
			break;
		}
		m++;
	}
	return h || d;
}, bE = (e) => [{
	words: Lt(e) ? [] : e.toString().split(dE),
	width: void 0
}], xE = (e) => {
	var t = e.width, n = e.scaleToFit, r = e.children, i = e.style, a = e.breakAll, o = e.maxLines;
	if ((t || n) && !El.isSsr) {
		var s, c, l = fE({
			breakAll: a,
			children: r,
			style: i
		});
		if (l) {
			var u = l.wordsWithComputedWidth, d = l.spaceWidth;
			s = u, c = d;
		} else return bE(r);
		return yE({
			breakAll: a,
			children: r,
			maxLines: o,
			style: i
		}, s, c, t, !!n);
	}
	return bE(r);
}, SE = "#808080", CE = {
	angle: 0,
	breakAll: !1,
	capHeight: "0.71em",
	fill: SE,
	lineHeight: "1em",
	scaleToFit: !1,
	textAnchor: "start",
	verticalAnchor: "end",
	x: 0,
	y: 0
}, wE = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = Yt(e, CE), r = n.x, i = n.y, a = n.lineHeight, o = n.capHeight, s = n.fill, c = n.scaleToFit, l = n.textAnchor, u = n.verticalAnchor, d = rE(n, eE), f = (0, C.useMemo)(() => xE({
		breakAll: d.breakAll,
		children: d.children,
		maxLines: d.maxLines,
		scaleToFit: c,
		style: d.style,
		width: d.width
	}), [
		d.breakAll,
		d.children,
		d.maxLines,
		c,
		d.style,
		d.width
	]), p = d.dx, m = d.dy, h = d.angle, g = d.className, _ = d.breakAll, v = rE(d, tE);
	if (!At(r) || !At(i) || f.length === 0) return null;
	var y = Number(r) + (I(p) ? p : 0), b = Number(i) + (I(m) ? m : 0);
	if (!q(y) || !q(b)) return null;
	var x;
	switch (u) {
		case "start":
			x = $T(`calc(${o})`);
			break;
		case "middle":
			x = $T(`calc(${(f.length - 1) / 2} * -${a} + (${o} / 2))`);
			break;
		default:
			x = $T(`calc(${f.length - 1} * -${a})`);
			break;
	}
	var S = [], w = f[0];
	if (c && w != null) {
		var T = w.width, E = d.width;
		S.push(`scale(${I(E) && I(T) ? E / T : 1})`);
	}
	return h && S.push(`rotate(${h}, ${y}, ${b})`), S.length && (v.transform = S.join(" ")), /*#__PURE__*/ C.createElement("text", nE({}, ae(v), {
		ref: t,
		x: y,
		y: b,
		className: N("recharts-text", g),
		textAnchor: l,
		fill: s.includes("url") ? SE : s
	}), f.map((e, t) => {
		var n = e.words.join(_ ? "" : " ");
		return /*#__PURE__*/ C.createElement("tspan", {
			x: y,
			dy: t === 0 ? x : a,
			key: `${n}-${t}`
		}, n);
	}));
});
wE.displayName = "Text";
//#endregion
//#region node_modules/recharts/es6/cartesian/getCartesianPosition.js
function TE(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function EE(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? TE(Object(n), !0).forEach(function(t) {
			DE(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : TE(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function DE(e, t, n) {
	return (t = OE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function OE(e) {
	var t = kE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function kE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var AE = (e) => {
	var t = e.viewBox, n = e.position, r = e.offset, i = r === void 0 ? 0 : r, a = e.parentViewBox, o = e.clamp, s = Cc(t), c = s.x, l = s.y, u = s.height, d = s.upperWidth, f = s.lowerWidth, p = c, m = c + (d - f) / 2, h = (p + m) / 2, g = (d + f) / 2, _ = p + d / 2, v = u >= 0 ? 1 : -1, y = v * i, b = v > 0 ? "end" : "start", x = v > 0 ? "start" : "end", S = d >= 0 ? 1 : -1, C = S * i, w = S > 0 ? "end" : "start", T = S > 0 ? "start" : "end", E = a;
	if (n === "top") {
		var D = {
			x: p + d / 2,
			y: l - y,
			horizontalAnchor: "middle",
			verticalAnchor: b
		};
		return o && E && (D.height = Math.max(l - E.y, 0), D.width = d), D;
	}
	if (n === "bottom") {
		var O = {
			x: m + f / 2,
			y: l + u + y,
			horizontalAnchor: "middle",
			verticalAnchor: x
		};
		return o && E && (O.height = Math.max(E.y + E.height - (l + u), 0), O.width = f), O;
	}
	if (n === "left") {
		var k = {
			x: h - C,
			y: l + u / 2,
			horizontalAnchor: w,
			verticalAnchor: "middle"
		};
		return o && E && (k.width = Math.max(k.x - E.x, 0), k.height = u), k;
	}
	if (n === "right") {
		var A = {
			x: h + g + C,
			y: l + u / 2,
			horizontalAnchor: T,
			verticalAnchor: "middle"
		};
		return o && E && (A.width = Math.max(E.x + E.width - A.x, 0), A.height = u), A;
	}
	var j = o && E ? {
		width: g,
		height: u
	} : {};
	return n === "insideLeft" ? EE({
		x: h + C,
		y: l + u / 2,
		horizontalAnchor: T,
		verticalAnchor: "middle"
	}, j) : n === "insideRight" ? EE({
		x: h + g - C,
		y: l + u / 2,
		horizontalAnchor: w,
		verticalAnchor: "middle"
	}, j) : n === "insideTop" ? EE({
		x: p + d / 2,
		y: l + y,
		horizontalAnchor: "middle",
		verticalAnchor: x
	}, j) : n === "insideBottom" ? EE({
		x: m + f / 2,
		y: l + u - y,
		horizontalAnchor: "middle",
		verticalAnchor: b
	}, j) : n === "insideTopLeft" ? EE({
		x: p + C,
		y: l + y,
		horizontalAnchor: T,
		verticalAnchor: x
	}, j) : n === "insideTopRight" ? EE({
		x: p + d - C,
		y: l + y,
		horizontalAnchor: w,
		verticalAnchor: x
	}, j) : n === "insideBottomLeft" ? EE({
		x: m + C,
		y: l + u - y,
		horizontalAnchor: T,
		verticalAnchor: b
	}, j) : n === "insideBottomRight" ? EE({
		x: m + f - C,
		y: l + u - y,
		horizontalAnchor: w,
		verticalAnchor: b
	}, j) : n && typeof n == "object" && (I(n.x) || kt(n.x)) && (I(n.y) || kt(n.y)) ? EE({
		x: c + Nt(n.x, g),
		y: l + Nt(n.y, u),
		horizontalAnchor: "end",
		verticalAnchor: "end"
	}, j) : EE({
		x: _,
		y: l + u / 2,
		horizontalAnchor: "middle",
		verticalAnchor: "middle"
	}, j);
}, jE = ["labelRef"], ME = ["content"];
function NE(e, t) {
	if (e == null) return {};
	var n, r, i = PE(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function PE(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function FE(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function IE(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? FE(Object(n), !0).forEach(function(t) {
			LE(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : FE(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function LE(e, t, n) {
	return (t = RE(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function RE(e) {
	var t = zE(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function zE(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function BE() {
	return BE = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, BE.apply(null, arguments);
}
var VE = /*#__PURE__*/ (0, C.createContext)(null), HE = (e) => {
	var t = e.x, n = e.y, r = e.upperWidth, i = e.lowerWidth, a = e.width, o = e.height, s = e.children, c = (0, C.useMemo)(() => ({
		x: t,
		y: n,
		upperWidth: r,
		lowerWidth: i,
		width: a,
		height: o
	}), [
		t,
		n,
		r,
		i,
		a,
		o
	]);
	return /*#__PURE__*/ C.createElement(VE.Provider, { value: c }, s);
}, UE = () => {
	var e = (0, C.useContext)(VE), t = wc();
	return e || (t ? Cc(t) : void 0);
}, WE = /*#__PURE__*/ (0, C.createContext)(null), GE = () => {
	var e = (0, C.useContext)(WE), t = z(Sp);
	return e || t;
}, KE = (e) => {
	var t = e.value, n = e.formatter, r = Lt(e.children) ? t : e.children;
	return typeof n == "function" ? n(r) : r;
}, qE = (e) => e != null && typeof e == "function", JE = (e, t) => Dt(t - e) * Math.min(Math.abs(t - e), 360), YE = (e, t, n, r, i) => {
	var a = e.offset, o = e.className, s = i.cx, c = i.cy, l = i.innerRadius, u = i.outerRadius, d = i.startAngle, f = i.endAngle, p = i.clockWise, m = (l + u) / 2, h = JE(d, f), g = h >= 0 ? 1 : -1, _, v;
	switch (t) {
		case "insideStart":
			_ = d + g * a, v = p;
			break;
		case "insideEnd":
			_ = f - g * a, v = !p;
			break;
		case "end":
			_ = f + g * a, v = p;
			break;
		default: throw Error(`Unsupported position ${t}`);
	}
	v = h <= 0 ? v : !v;
	var y = Vd(s, c, m, _), b = Vd(s, c, m, _ + (v ? 1 : -1) * 359), x = `M${y.x},${y.y}
    A${m},${m},0,1,${+!v},
    ${b.x},${b.y}`, S = Lt(e.id) ? Mt("recharts-radial-line-") : e.id;
	return /*#__PURE__*/ C.createElement("text", BE({}, r, {
		dominantBaseline: "central",
		className: N("recharts-radial-bar-label", o)
	}), /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("path", {
		id: S,
		d: x
	})), /*#__PURE__*/ C.createElement("textPath", { xlinkHref: `#${S}` }, n));
}, XE = (e, t, n) => {
	var r = e.cx, i = e.cy, a = e.innerRadius, o = e.outerRadius, s = (e.startAngle + e.endAngle) / 2;
	if (n === "outside") {
		var c = Vd(r, i, o + t, s), l = c.x;
		return {
			x: l,
			y: c.y,
			textAnchor: l >= r ? "start" : "end",
			verticalAnchor: "middle"
		};
	}
	if (n === "center") return {
		x: r,
		y: i,
		textAnchor: "middle",
		verticalAnchor: "middle"
	};
	if (n === "centerTop") return {
		x: r,
		y: i,
		textAnchor: "middle",
		verticalAnchor: "start"
	};
	if (n === "centerBottom") return {
		x: r,
		y: i,
		textAnchor: "middle",
		verticalAnchor: "end"
	};
	var u = Vd(r, i, (a + o) / 2, s);
	return {
		x: u.x,
		y: u.y,
		textAnchor: "middle",
		verticalAnchor: "middle"
	};
}, ZE = (e) => e != null && "cx" in e && I(e.cx), QE = {
	angle: 0,
	offset: 5,
	zIndex: np.label,
	position: "middle",
	textBreakAll: !1
};
function $E(e) {
	if (!ZE(e)) return e;
	var t = e.cx, n = e.cy, r = e.outerRadius, i = r * 2;
	return {
		x: t - r,
		y: n - r,
		width: i,
		upperWidth: i,
		lowerWidth: i,
		height: i
	};
}
function eD(e) {
	var t = Yt(e, QE), n = t.viewBox, r = t.parentViewBox, i = t.position, a = t.value, o = t.children, s = t.content, c = t.className, l = c === void 0 ? "" : c, u = t.textBreakAll, d = t.labelRef, f = GE(), p = UE(), m = n == null ? i === "center" || f == null ? p : f : ZE(n) ? n : Cc(n), h, g, _ = $E(m);
	if (!m || Lt(a) && Lt(o) && !/*#__PURE__*/ (0, C.isValidElement)(s) && typeof s != "function") return null;
	var v = IE(IE({}, t), {}, { viewBox: m });
	if (/*#__PURE__*/ (0, C.isValidElement)(s)) return v.labelRef, /*#__PURE__*/ (0, C.cloneElement)(s, NE(v, jE));
	if (typeof s == "function") {
		if (v.content, h = /*#__PURE__*/ (0, C.createElement)(s, NE(v, ME)), /*#__PURE__*/ (0, C.isValidElement)(h)) return h;
	} else h = KE(t);
	var y = ae(t);
	if (ZE(m)) {
		if (i === "insideStart" || i === "insideEnd" || i === "end") return YE(t, i, h, y, m);
		g = XE(m, t.offset, t.position);
	} else {
		if (!_) return null;
		var b = AE({
			viewBox: _,
			position: i,
			offset: t.offset,
			parentViewBox: ZE(r) ? void 0 : r,
			clamp: !0
		});
		g = IE(IE({
			x: b.x,
			y: b.y,
			textAnchor: b.horizontalAnchor,
			verticalAnchor: b.verticalAnchor
		}, b.width === void 0 ? {} : { width: b.width }), b.height === void 0 ? {} : { height: b.height });
	}
	return /*#__PURE__*/ C.createElement(dw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(wE, BE({
		ref: d,
		className: N("recharts-label", l)
	}, y, g, {
		textAnchor: pE(y.textAnchor) ? y.textAnchor : g.textAnchor,
		breakAll: u
	}), h));
}
eD.displayName = "Label";
var tD = (e, t, n) => {
	if (!e) return null;
	var r = {
		viewBox: t,
		labelRef: n
	};
	return e === !0 ? /*#__PURE__*/ C.createElement(eD, BE({ key: "label-implicit" }, r)) : At(e) ? /*#__PURE__*/ C.createElement(eD, BE({
		key: "label-implicit",
		value: e
	}, r)) : /*#__PURE__*/ (0, C.isValidElement)(e) ? e.type === eD ? /*#__PURE__*/ (0, C.cloneElement)(e, IE({ key: "label-implicit" }, r)) : /*#__PURE__*/ C.createElement(eD, BE({
		key: "label-implicit",
		content: e
	}, r)) : qE(e) ? /*#__PURE__*/ C.createElement(eD, BE({
		key: "label-implicit",
		content: e
	}, r)) : e && typeof e == "object" ? /*#__PURE__*/ C.createElement(eD, BE({}, e, { key: "label-implicit" }, r)) : null;
};
function nD(e) {
	var t = e.label, n = e.labelRef;
	return tD(t, UE(), n) || null;
}
//#endregion
//#region node_modules/recharts/es6/component/LabelList.js
var rD = ["valueAccessor"], iD = [
	"dataKey",
	"clockWise",
	"id",
	"textBreakAll",
	"zIndex"
];
function aD() {
	return aD = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, aD.apply(null, arguments);
}
function oD(e, t) {
	if (e == null) return {};
	var n, r, i = sD(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function sD(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var cD = (e) => {
	var t = Array.isArray(e.value) ? e.value[e.value.length - 1] : e.value;
	if (mE(t)) return t;
}, lD = /*#__PURE__*/ (0, C.createContext)(void 0), uD = lD.Provider, dD = /*#__PURE__*/ (0, C.createContext)(void 0);
dD.Provider;
function fD() {
	return (0, C.useContext)(lD);
}
function pD() {
	return (0, C.useContext)(dD);
}
function mD(e) {
	var t = e.valueAccessor, n = t === void 0 ? cD : t, r = oD(e, rD), i = r.dataKey;
	r.clockWise;
	var a = r.id, o = r.textBreakAll, s = r.zIndex, c = oD(r, iD), l = fD(), u = pD(), d = l || u;
	return !d || !d.length ? null : /*#__PURE__*/ C.createElement(dw, { zIndex: s == null ? np.label : s }, /*#__PURE__*/ C.createElement(he, { className: "recharts-label-list" }, d.map((e, t) => {
		var s, l = Lt(i) ? n(e, t) : ns(e.payload, i), u = Lt(a) ? {} : { id: `${a}-${t}` };
		return /*#__PURE__*/ C.createElement(eD, aD({ key: `label-${t}` }, ae(e), c, u, {
			fill: (s = r.fill) == null ? e.fill : s,
			parentViewBox: e.parentViewBox,
			value: l,
			textBreakAll: o,
			viewBox: e.viewBox,
			index: t,
			zIndex: 0
		}));
	})));
}
mD.displayName = "LabelList";
function hD(e) {
	var t = e.label;
	return t ? t === !0 ? /*#__PURE__*/ C.createElement(mD, { key: "labelList-implicit" }) : /*#__PURE__*/ C.isValidElement(t) || qE(t) ? /*#__PURE__*/ C.createElement(mD, {
		key: "labelList-implicit",
		content: t
	}) : typeof t == "object" ? /*#__PURE__*/ C.createElement(mD, aD({ key: "labelList-implicit" }, t, { type: String(t.type) })) : null : null;
}
//#endregion
//#region node_modules/recharts/es6/state/polarAxisSlice.js
var gD = eo({
	name: "polarAxis",
	initialState: {
		radiusAxis: {},
		angleAxis: {}
	},
	reducers: {
		addRadiusAxis(e, t) {
			e.radiusAxis[t.payload.id] = W(t.payload);
		},
		removeRadiusAxis(e, t) {
			delete e.radiusAxis[t.payload.id];
		},
		addAngleAxis(e, t) {
			e.angleAxis[t.payload.id] = W(t.payload);
		},
		removeAngleAxis(e, t) {
			delete e.angleAxis[t.payload.id];
		}
	}
}), _D = gD.actions;
_D.addRadiusAxis, _D.removeRadiusAxis, _D.addAngleAxis, _D.removeAngleAxis;
var vD = gD.reducer;
//#endregion
//#region node_modules/recharts/es6/util/getClassNameFromUnknown.js
function yD(e) {
	return e && typeof e == "object" && "className" in e && typeof e.className == "string" ? e.className : "";
}
//#endregion
//#region node_modules/react-is/cjs/react-is.production.min.js
var bD = /* @__PURE__ */ o(((e) => {
	var t = 60103, n = 60106, r = 60107, i = 60108, a = 60114, o = 60109, s = 60110, c = 60112, l = 60113, u = 60120, d = 60115, f = 60116;
	if (typeof Symbol == "function" && Symbol.for) {
		var p = Symbol.for;
		t = p("react.element"), n = p("react.portal"), r = p("react.fragment"), i = p("react.strict_mode"), a = p("react.profiler"), o = p("react.provider"), s = p("react.context"), c = p("react.forward_ref"), l = p("react.suspense"), u = p("react.suspense_list"), d = p("react.memo"), f = p("react.lazy"), p("react.block"), p("react.server.block"), p("react.fundamental"), p("react.debug_trace_mode"), p("react.legacy_hidden");
	}
	function m(e) {
		if (typeof e == "object" && e) {
			var p = e.$$typeof;
			switch (p) {
				case t: switch (e = e.type, e) {
					case r:
					case a:
					case i:
					case l:
					case u: return e;
					default: switch (e = e && e.$$typeof, e) {
						case s:
						case c:
						case f:
						case d:
						case o: return e;
						default: return p;
					}
				}
				case n: return p;
			}
		}
	}
	e.isFragment = function(e) {
		return m(e) === r;
	};
})), xD = (/* @__PURE__ */ o(((e, t) => {
	t.exports = bD();
})))(), SD = (e) => typeof e == "string" ? e : e ? e.displayName || e.name || "Component" : "", CD = null, wD = null, TD = (e) => {
	if (e === CD && Array.isArray(wD)) return wD;
	var t = [];
	return C.Children.forEach(e, (e) => {
		Lt(e) || ((0, xD.isFragment)(e) ? t = t.concat(TD(e.props.children)) : t.push(e));
	}), wD = t, CD = e, t;
};
function ED(e, t) {
	var n = [], r = [];
	return r = Array.isArray(t) ? t.map((e) => SD(e)) : [SD(t)], TD(e).forEach((e) => {
		var t = St(e, "type.displayName") || St(e, "type.name");
		t && r.indexOf(t) !== -1 && n.push(e);
	}), n;
}
//#endregion
//#region node_modules/recharts/es6/util/ActiveShapeUtils.js
function DD(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function OD(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? DD(Object(n), !0).forEach(function(t) {
			kD(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : DD(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function kD(e, t, n) {
	return (t = AD(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function AD(e) {
	var t = jD(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function jD(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function MD(e, t) {
	return OD(OD({}, t), e);
}
function ND(e) {
	return /*#__PURE__*/ (0, C.isValidElement)(e) ? e.props : e;
}
function PD(e, t) {
	return /*#__PURE__*/ (0, C.cloneElement)(e, MD(ND(e), t));
}
function FD(e) {
	if ("index" in e) {
		var t = e.index;
		return typeof t == "number" || typeof t == "string" ? t : void 0;
	}
}
function ID(e) {
	return "isActive" in e && e.isActive === !0;
}
function LD(e) {
	var t = e.option, n = e.DefaultShape, r = e.shapeProps, i = e.activeClassName, a = i === void 0 ? "recharts-active-shape" : i, o = e.inActiveClassName, s = o === void 0 ? "recharts-shape" : o, c = FD(r), l = /*#__PURE__*/ (0, C.isValidElement)(t) ? PD(t, r) : t === n ? /*#__PURE__*/ C.createElement(n, r) : typeof t == "function" ? t(r, c) : typeof t == "object" ? /*#__PURE__*/ C.createElement(n, MD(t, r)) : /*#__PURE__*/ C.createElement(n, r);
	return ID(r) ? /*#__PURE__*/ C.createElement(he, { className: a }, l) : /*#__PURE__*/ C.createElement(he, { className: s }, l);
}
//#endregion
//#region node_modules/recharts/es6/context/tooltipContext.js
var RD = (e, t, n) => {
	var r = R();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(eS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
}, zD = (e) => {
	var t = R();
	return (n, r) => (i) => {
		e == null || e(n, r, i), t(tS());
	};
}, BD = (e, t, n) => {
	var r = R();
	return (i, a) => (o) => {
		e == null || e(i, a, o), r(rS({
			activeIndex: String(a),
			activeDataKey: t,
			activeCoordinate: i.tooltipPosition,
			activeGraphicalItemId: n
		}));
	};
};
//#endregion
//#region node_modules/recharts/es6/state/SetTooltipEntrySettings.js
function VD(e) {
	var t = e.tooltipEntrySettings, n = R(), r = Hs(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(Xx(t)) : i.current !== t && n(Zx({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		t,
		n,
		r
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(Qx(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/state/SetLegendPayload.js
function HD(e) {
	var t = e.legendPayload, n = R(), r = Hs(), i = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		r || (i.current === null ? n(Ic(t)) : i.current !== t && n(Lc({
			prev: i.current,
			next: t
		})), i.current = t);
	}, [
		n,
		r,
		t
	]), (0, C.useLayoutEffect)(() => () => {
		i.current && (n(Rc(i.current)), i.current = null);
	}, [n]), null;
}
//#endregion
//#region node_modules/recharts/es6/animation/matchBy.js
function UD(e, t) {
	return JD(e) || qD(e, t) || GD(e, t) || WD();
}
function WD() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function GD(e, t) {
	if (e) {
		if (typeof e == "string") return KD(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? KD(e, t) : void 0;
	}
}
function KD(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function qD(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function JD(e) {
	if (Array.isArray(e)) return e;
}
var YD = "index", XD = "append";
function ZD(e, t) {
	var n = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : [], r = [];
	for (var i of n) r.push({
		status: "removed",
		prev: i
	});
	for (var a = 0; a < t.length; a++) {
		var o = e[a], s = t[a];
		o == null ? r.push({
			status: "added",
			next: s
		}) : r.push({
			status: "matched",
			prev: o,
			next: s
		});
	}
	return r;
}
function QD(e, t) {
	var n = e.length / t.length;
	return ZD(t.map((t, r) => e[Math.floor(r * n)]), t);
}
function $D(e, t) {
	return ZD(t.map((t, n) => e[n]), t);
}
function eO(e, t) {
	for (var n = /* @__PURE__ */ new Map(), r = 0; r < e.length; r++) {
		var i = e[r];
		if (i != null) {
			var a = t(i, r);
			a != null && !n.has(a) && n.set(a, i);
		}
	}
	return n;
}
function tO(e, t, n) {
	var r = eO(e, n), i = /* @__PURE__ */ new Set(), a = t.map((e, t) => {
		var a = n(e, t);
		if (a != null) {
			var o = r.get(a);
			if (o !== void 0) return i.add(a), o;
		}
	}), o = [];
	for (var s of r) {
		var c = UD(s, 2), l = c[0], u = c[1];
		i.has(l) || o.push(u);
	}
	return ZD(a, t, o);
}
function nO(e, t, n) {
	return t == null ? null : e == null ? t.map((e) => ({
		status: "added",
		next: e
	})) : n === "index" ? QD(e, t) : n === "append" ? $D(e, t) : tO(e, t, n);
}
//#endregion
//#region node_modules/recharts/es6/animation/useAnimationStartSnapshot.js
function rO(e, t) {
	var n = (0, C.useRef)(e), r = (0, C.useRef)(t.current), i = (0, C.useRef)(!0);
	n.current !== e && (n.current = e, r.current = t.current, i.current = !1);
	var a = (0, C.useCallback)(function(e, n) {
		var a = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : !0;
		if (n === 0) {
			i.current = !0;
			return;
		}
		n === 1 && (r.current = e), n > 0 && i.current && a && (t.current = e);
	}, [t]);
	return {
		startValue: r.current,
		syncStepValue: a
	};
}
//#endregion
//#region node_modules/recharts/es6/animation/AnimatedItems.js
function iO(e, t) {
	return lO(e) || cO(e, t) || oO(e, t) || aO();
}
function aO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function oO(e, t) {
	if (e) {
		if (typeof e == "string") return sO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? sO(e, t) : void 0;
	}
}
function sO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function cO(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function lO(e) {
	if (Array.isArray(e)) return e;
}
function uO(e, t) {
	var n = iO((0, C.useState)(!1), 2), r = n[0], i = n[1];
	return {
		isAnimating: r,
		handleAnimationStart: (0, C.useCallback)(() => {
			typeof e == "function" && e(), i(!0);
		}, [e]),
		handleAnimationEnd: (0, C.useCallback)(() => {
			typeof t == "function" && t(), i(!1);
		}, [t])
	};
}
function dO(e) {
	var t, n = e.animationInput, r = e.animationIdPrefix, i = e.items, a = e.previousItemsRef, o = e.isAnimationActive, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.onAnimationStart, d = e.onAnimationEnd, f = e.animationInterpolateFn, p = e.animationMatchBy, m = e.shouldUpdatePreviousRef, h = e.children, g = e.layout, _ = td(n, r), v = rO(_, a), y = (t = v.startValue) == null ? null : t, b = nO(y, i, p == null ? YD : p);
	return /*#__PURE__*/ C.createElement(ed, {
		animationId: _,
		begin: s,
		duration: c,
		isActive: o,
		easing: l,
		onAnimationEnd: d,
		onAnimationStart: u,
		key: _
	}, (e) => {
		var t = y == null, n = i == null ? i : f(b, e, g), r = m ? m(e) : e > 0;
		return v.syncStepValue(n, e, r), n == null ? null : h(n, e, t);
	});
}
//#endregion
//#region node_modules/recharts/es6/util/useId.js
var fO;
function pO(e, t) {
	return vO(e) || _O(e, t) || hO(e, t) || mO();
}
function mO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function hO(e, t) {
	if (e) {
		if (typeof e == "string") return gO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? gO(e, t) : void 0;
	}
}
function gO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function _O(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function vO(e) {
	if (Array.isArray(e)) return e;
}
var yO = (fO = C.useId) == null ? () => pO(C.useState(() => Mt("uid-")), 1)[0] : fO;
//#endregion
//#region node_modules/recharts/es6/util/useUniqueId.js
function bO(e, t) {
	var n = yO();
	return t || (e ? `${e}-${n}` : n);
}
//#endregion
//#region node_modules/recharts/es6/context/RegisterGraphicalItemId.js
var xO = /*#__PURE__*/ (0, C.createContext)(void 0), SO = (e) => {
	var t = e.id, n = e.type, r = e.children, i = bO(`recharts-${n}`, t);
	return /*#__PURE__*/ C.createElement(xO.Provider, { value: i }, r(i));
}, CO = eo({
	name: "graphicalItems",
	initialState: {
		cartesianItems: [],
		polarItems: []
	},
	reducers: {
		addCartesianGraphicalItem: {
			reducer(e, t) {
				e.cartesianItems.push(W(t.payload));
			},
			prepare: G()
		},
		replaceCartesianGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ea(e).cartesianItems.indexOf(W(r));
				a > -1 && (e.cartesianItems[a] = W(i));
			},
			prepare: G()
		},
		removeCartesianGraphicalItem: {
			reducer(e, t) {
				var n = Ea(e).cartesianItems.indexOf(W(t.payload));
				n > -1 && e.cartesianItems.splice(n, 1);
			},
			prepare: G()
		},
		addPolarGraphicalItem: {
			reducer(e, t) {
				e.polarItems.push(W(t.payload));
			},
			prepare: G()
		},
		removePolarGraphicalItem: {
			reducer(e, t) {
				var n = Ea(e).polarItems.indexOf(W(t.payload));
				n > -1 && e.polarItems.splice(n, 1);
			},
			prepare: G()
		},
		replacePolarGraphicalItem: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next, a = Ea(e).polarItems.indexOf(W(r));
				a > -1 && (e.polarItems[a] = W(i));
			},
			prepare: G()
		}
	}
}), wO = CO.actions, TO = wO.addCartesianGraphicalItem, EO = wO.replaceCartesianGraphicalItem, DO = wO.removeCartesianGraphicalItem;
wO.addPolarGraphicalItem, wO.removePolarGraphicalItem, wO.replacePolarGraphicalItem;
var OO = CO.reducer, kO = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = R(), n = (0, C.useRef)(null);
	return (0, C.useLayoutEffect)(() => {
		n.current === null ? t(TO(e)) : n.current !== e && t(EO({
			prev: n.current,
			next: e
		})), n.current = e;
	}, [t, e]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(DO(n.current)), n.current = null);
	}, [t]), null;
});
//#endregion
//#region node_modules/recharts/es6/state/cartesianAxisSlice.js
function AO(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function jO(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? AO(Object(n), !0).forEach(function(t) {
			MO(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : AO(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function MO(e, t, n) {
	return (t = NO(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function NO(e) {
	var t = PO(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function PO(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var FO = eo({
	name: "cartesianAxis",
	initialState: {
		xAxis: {},
		yAxis: {},
		zAxis: {}
	},
	reducers: {
		addXAxis: {
			reducer(e, t) {
				e.xAxis[t.payload.id] = W(t.payload);
			},
			prepare: G()
		},
		replaceXAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.xAxis[r.id] !== void 0 && (r.id !== i.id && delete e.xAxis[r.id], e.xAxis[i.id] = W(i));
			},
			prepare: G()
		},
		removeXAxis: {
			reducer(e, t) {
				delete e.xAxis[t.payload.id];
			},
			prepare: G()
		},
		addYAxis: {
			reducer(e, t) {
				e.yAxis[t.payload.id] = W(t.payload);
			},
			prepare: G()
		},
		replaceYAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.yAxis[r.id] !== void 0 && (r.id !== i.id && delete e.yAxis[r.id], e.yAxis[i.id] = W(i));
			},
			prepare: G()
		},
		removeYAxis: {
			reducer(e, t) {
				delete e.yAxis[t.payload.id];
			},
			prepare: G()
		},
		addZAxis: {
			reducer(e, t) {
				e.zAxis[t.payload.id] = W(t.payload);
			},
			prepare: G()
		},
		replaceZAxis: {
			reducer(e, t) {
				var n = t.payload, r = n.prev, i = n.next;
				e.zAxis[r.id] !== void 0 && (r.id !== i.id && delete e.zAxis[r.id], e.zAxis[i.id] = W(i));
			},
			prepare: G()
		},
		removeZAxis: {
			reducer(e, t) {
				delete e.zAxis[t.payload.id];
			},
			prepare: G()
		},
		updateYAxisWidth(e, t) {
			var n = t.payload, r = n.id, i = n.width, a = e.yAxis[r];
			if (a) {
				var o, s = a.widthHistory || [];
				if (s.length === 3 && s[0] === s[2] && i === s[1] && i !== a.width && Math.abs(i - ((o = s[0]) == null ? 0 : o)) <= 1) return;
				var c = [...s, i].slice(-3);
				e.yAxis[r] = jO(jO({}, a), {}, {
					width: i,
					widthHistory: c
				});
			}
		}
	}
}), IO = FO.actions, LO = IO.addXAxis, RO = IO.replaceXAxis, zO = IO.removeXAxis, BO = IO.addYAxis, VO = IO.replaceYAxis, HO = IO.removeYAxis;
IO.addZAxis, IO.replaceZAxis, IO.removeZAxis;
var UO = IO.updateYAxisWidth, WO = FO.reducer, GO = B([
	B([Rs], (e) => ({
		top: e.top,
		bottom: e.bottom,
		left: e.left,
		right: e.right
	})),
	xs,
	Ss
], (e, t, n) => {
	if (!(!e || t == null || n == null)) return {
		x: e.left,
		y: e.top,
		width: Math.max(0, t - e.left - e.right),
		height: Math.max(0, n - e.top - e.bottom)
	};
}), KO = () => z(GO);
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineBarSizeList.js
function qO(e, t) {
	return QO(e) || ZO(e, t) || YO(e, t) || JO();
}
function JO() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function YO(e, t) {
	if (e) {
		if (typeof e == "string") return XO(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? XO(e, t) : void 0;
	}
}
function XO(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function ZO(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function QO(e) {
	if (Array.isArray(e)) return e;
}
var $O = (e, t, n) => {
	var r = n == null ? e : n;
	if (!Lt(r)) return Nt(r, t, 0);
}, ek = (e, t, n) => {
	var r = {}, i = e.filter(Dp), a = e.filter((e) => e.stackId == null), o = i.reduce((e, t) => {
		var n = e[t.stackId];
		return n == null && (n = []), n.push(t), e[t.stackId] = n, e;
	}, r), s = Object.entries(o).map((e) => {
		var r, i = qO(e, 2), a = i[0], o = i[1];
		return {
			stackId: a,
			dataKeys: o.map((e) => e.dataKey),
			barSize: $O(t, n, (r = o[0]) == null ? void 0 : r.barSize)
		};
	}), c = a.map((e) => ({
		stackId: void 0,
		dataKeys: [e.dataKey].filter((e) => e != null),
		barSize: $O(t, n, e.barSize)
	}));
	return [...s, ...c];
};
//#endregion
//#region node_modules/recharts/es6/state/selectors/combiners/combineAllBarPositions.js
function tk(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function nk(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? tk(Object(n), !0).forEach(function(t) {
			rk(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : tk(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function rk(e, t, n) {
	return (t = ik(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function ik(e) {
	var t = ak(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function ak(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function ok(e, t, n, r, i) {
	var a, o = r.length;
	if (!(o < 1)) {
		var s = Nt(e, n, 0, !0), c, l = [];
		if (q((a = r[0]) == null ? void 0 : a.barSize)) {
			var u = !1, d = n / o, f = r.reduce((e, t) => e + (t.barSize || 0), 0);
			f += (o - 1) * s, f >= n && (f -= (o - 1) * s, s = 0), f >= n && d > 0 && (u = !0, d *= .9, f = o * d);
			var p = {
				offset: Math.round((n - f) / 2) - s,
				size: 0
			};
			c = r.reduce((e, t) => {
				var n, r = {
					stackId: t.stackId,
					dataKeys: t.dataKeys,
					position: {
						offset: p.offset + p.size + s,
						size: u ? d : (n = t.barSize) == null ? 0 : n
					}
				}, i = [...e, r];
				return p = r.position, i;
			}, l);
		} else {
			var m = Nt(t, n, 0, !0);
			n - 2 * m - (o - 1) * s <= 0 && (s = 0);
			var h = (n - 2 * m - (o - 1) * s) / o;
			h > 1 && (h = Math.round(h));
			var g = q(i) ? Math.min(h, i) : h;
			c = r.reduce((e, t, n) => [...e, {
				stackId: t.stackId,
				dataKeys: t.dataKeys,
				position: {
					offset: m + (h + s) * n + (h - g) / 2,
					size: g
				}
			}], l);
		}
		return c;
	}
}
var sk = (e, t, n, r, i, a, o) => {
	var s = Lt(o) ? t : o, c = ok(n, r, i === a ? a : i, e, s);
	return i !== a && c != null && (c = c.map((e) => nk(nk({}, e), {}, { position: nk(nk({}, e.position), {}, { offset: e.position.offset - i / 2 }) }))), c;
}, ck = (e, t) => {
	var n = Tp(t);
	if (!(!e || n == null || t == null)) {
		var r = t.stackId;
		if (r != null) {
			var i = e[r];
			if (i) {
				var a = i.stackedData;
				if (a) return a.find((e) => e.key === n);
			}
		}
	}
}, lk = (e, t) => {
	if (!(e == null || t == null)) {
		var n = e.find((e) => e.stackId === t.stackId && t.dataKey != null && e.dataKeys.includes(t.dataKey));
		if (n != null) return n.position;
	}
};
//#endregion
//#region node_modules/recharts/es6/zIndex/getZIndexFromUnknown.js
function uk(e, t) {
	return e && typeof e == "object" && "zIndex" in e && typeof e.zIndex == "number" && q(e.zIndex) ? e.zIndex : t;
}
//#endregion
//#region node_modules/recharts/es6/context/chartDataContext.js
var dk = (e) => {
	var t = e.chartData, n = R(), r = Hs();
	return (0, C.useEffect)(() => r ? () => {} : (n(Pw(t)), () => {
		n(Pw(void 0));
	}), [
		t,
		n,
		r
	]), null;
}, fk = {
	x: 0,
	y: 0,
	width: 0,
	height: 0,
	padding: {
		top: 0,
		right: 0,
		bottom: 0,
		left: 0
	}
}, pk = eo({
	name: "brush",
	initialState: fk,
	reducers: { setBrushSettings(e, t) {
		return t.payload == null ? fk : t.payload;
	} }
});
pk.actions.setBrushSettings;
var mk = pk.reducer;
//#endregion
//#region node_modules/recharts/es6/util/CartesianUtils.js
function hk(e) {
	return (e % 180 + 180) % 180;
}
var gk = function(e) {
	var t = e.width, n = e.height, r = hk(arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0) * Math.PI / 180, i = Math.atan(n / t), a = r > i && r < Math.PI - i ? n / Math.sin(r) : t / Math.cos(r);
	return Math.abs(a);
}, _k = eo({
	name: "referenceElements",
	initialState: {
		dots: [],
		areas: [],
		lines: []
	},
	reducers: {
		addDot: (e, t) => {
			e.dots.push(t.payload);
		},
		removeDot: (e, t) => {
			var n = Ea(e).dots.findIndex((e) => e === t.payload);
			n !== -1 && e.dots.splice(n, 1);
		},
		addArea: (e, t) => {
			e.areas.push(t.payload);
		},
		removeArea: (e, t) => {
			var n = Ea(e).areas.findIndex((e) => e === t.payload);
			n !== -1 && e.areas.splice(n, 1);
		},
		addLine: (e, t) => {
			e.lines.push(W(t.payload));
		},
		removeLine: (e, t) => {
			var n = Ea(e).lines.findIndex((e) => e === t.payload);
			n !== -1 && e.lines.splice(n, 1);
		}
	}
}), vk = _k.actions;
vk.addDot, vk.removeDot, vk.addArea, vk.removeArea, vk.addLine, vk.removeLine;
var yk = _k.reducer;
//#endregion
//#region node_modules/recharts/es6/container/ClipPathProvider.js
function bk(e, t) {
	return Tk(e) || wk(e, t) || Sk(e, t) || xk();
}
function xk() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Sk(e, t) {
	if (e) {
		if (typeof e == "string") return Ck(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? Ck(e, t) : void 0;
	}
}
function Ck(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function wk(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function Tk(e) {
	if (Array.isArray(e)) return e;
}
var Ek = /*#__PURE__*/ (0, C.createContext)(void 0), Dk = (e) => {
	var t = e.children, n = bk((0, C.useState)(`${Mt("recharts")}-clip`), 1)[0], r = KO();
	if (r == null) return null;
	var i = r.x, a = r.y, o = r.width, s = r.height;
	return /*#__PURE__*/ C.createElement(Ek.Provider, { value: n }, /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement("clipPath", { id: n }, /*#__PURE__*/ C.createElement("rect", {
		x: i,
		y: a,
		height: s,
		width: o
	}))), t);
};
//#endregion
//#region node_modules/recharts/es6/util/getEveryNth.js
function Ok(e, t) {
	if (t < 1) return [];
	if (t === 1) return e;
	for (var n = [], r = 0; r < e.length; r += t) {
		var i = e[r];
		i !== void 0 && n.push(i);
	}
	return n;
}
//#endregion
//#region node_modules/recharts/es6/util/TickUtils.js
function kk(e, t, n) {
	return gk({
		width: e.width + t.width,
		height: e.height + t.height
	}, n);
}
function Ak(e, t, n) {
	var r = n === "width", i = e.x, a = e.y, o = e.width, s = e.height;
	return t === 1 ? {
		start: r ? i : a,
		end: r ? i + o : a + s
	} : {
		start: r ? i + o : a + s,
		end: r ? i : a
	};
}
function jk(e, t, n, r, i) {
	if (e * t < e * r || e * t > e * i) return !1;
	var a = n();
	return e * (t - e * a / 2 - r) >= 0 && e * (t + e * a / 2 - i) <= 0;
}
function Mk(e, t) {
	return Ok(e, t + 1);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/getEquidistantTicks.js
function Nk(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = t.start, s = t.end, c = 0, l = 1, u = o, d = function() {
		var t = r == null ? void 0 : r[c];
		if (t === void 0) return { v: Ok(r, l) };
		var a = c, d, f = () => (d === void 0 && (d = n(t, a)), d), p = t.coordinate, m = c === 0 || jk(e, p, f, u, s);
		m || (c = 0, u = o, l += 1), m && (u = p + e * (f() / 2 + i), c += l);
	}, f; l <= a.length;) if (f = d(), f) return f.v;
	return [];
}
function Pk(e, t, n, r, i) {
	var a = (r || []).slice().length;
	if (a === 0) return [];
	for (var o = t.start, s = t.end, c = 1; c <= a; c++) {
		for (var l = (a - 1) % c, u = o, d = !0, f = function() {
			var t = r[m];
			if (t == null) return 0;
			var a = m, o, c = () => (o === void 0 && (o = n(t, a)), o), f = t.coordinate, p = m === l || jk(e, f, c, u, s);
			if (!p) return d = !1, 1;
			p && (u = f + e * (c() / 2 + i));
		}, p, m = l; m < a && (p = f(), !(p !== 0 && p === 1)); m += c);
		if (d) {
			for (var h = [], g = l; g < a; g += c) {
				var _ = r[g];
				_ != null && h.push(_);
			}
			return h;
		}
	}
	return [];
}
//#endregion
//#region node_modules/recharts/es6/cartesian/getTicks.js
function Fk(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Ik(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Fk(Object(n), !0).forEach(function(t) {
			Lk(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Fk(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function Lk(e, t, n) {
	return (t = Rk(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function Rk(e) {
	var t = zk(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function zk(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function Bk(e, t, n, r, i) {
	for (var a = (r || []).slice(), o = a.length, s = t.start, c = t.end, l = function(t) {
		var r = a[t];
		if (r == null) return 1;
		var l = r, u, d = () => (u === void 0 && (u = n(r, t)), u);
		if (t === o - 1) {
			var f = e * (l.coordinate + e * d() / 2 - c);
			a[t] = l = Ik(Ik({}, l), {}, { tickCoord: f > 0 ? l.coordinate - f * e : l.coordinate });
		} else a[t] = l = Ik(Ik({}, l), {}, { tickCoord: l.coordinate });
		l.tickCoord != null && jk(e, l.tickCoord, d, s, c) && (c = l.tickCoord - e * (d() / 2 + i), a[t] = Ik(Ik({}, l), {}, { isShow: !0 }));
	}, u = o - 1; u >= 0; u--) if (l(u)) continue;
	return a;
}
function Vk(e, t, n, r, i, a) {
	var o = (r || []).slice(), s = o.length, c = t.start, l = t.end;
	if (a) {
		var u = r[s - 1];
		if (u != null) {
			var d = n(u, s - 1), f = e * (u.coordinate + e * d / 2 - l);
			o[s - 1] = u = Ik(Ik({}, u), {}, { tickCoord: f > 0 ? u.coordinate - f * e : u.coordinate }), u.tickCoord != null && jk(e, u.tickCoord, () => d, c, l) && (l = u.tickCoord - e * (d / 2 + i), o[s - 1] = Ik(Ik({}, u), {}, { isShow: !0 }));
		}
	}
	for (var p = a ? s - 1 : s, m = function(t) {
		var r = o[t];
		if (r == null) return 1;
		var a = r, s, u = () => (s === void 0 && (s = n(r, t)), s);
		if (t === 0) {
			var d = e * (a.coordinate - e * u() / 2 - c);
			o[t] = a = Ik(Ik({}, a), {}, { tickCoord: d < 0 ? a.coordinate - d * e : a.coordinate });
		} else o[t] = a = Ik(Ik({}, a), {}, { tickCoord: a.coordinate });
		a.tickCoord != null && jk(e, a.tickCoord, u, c, l) && (c = a.tickCoord + e * (u() / 2 + i), o[t] = Ik(Ik({}, a), {}, { isShow: !0 }));
	}, h = 0; h < p; h++) if (m(h)) continue;
	return o;
}
function Hk(e, t, n) {
	var r = e.tick, i = e.ticks, a = e.viewBox, o = e.minTickGap, s = e.orientation, c = e.interval, l = e.tickFormatter, u = e.unit, d = e.angle;
	if (!i || !i.length || !r) return [];
	if (I(c) || El.isSsr) {
		var f;
		return (f = Mk(i, I(c) ? c : 0)) == null ? [] : f;
	}
	var p = [], m = s === "top" || s === "bottom" ? "width" : "height", h = u && m === "width" ? DT(u, {
		fontSize: t,
		letterSpacing: n
	}) : {
		width: 0,
		height: 0
	}, g = (e, r) => {
		var i = typeof l == "function" ? l(e.value, r) : e.value;
		return m === "width" ? kk(DT(i, {
			fontSize: t,
			letterSpacing: n
		}), h, d) : DT(i, {
			fontSize: t,
			letterSpacing: n
		})[m];
	}, _ = i[0], v = i[1], y = i.length >= 2 && _ != null && v != null ? Dt(v.coordinate - _.coordinate) : 1, b = Ak(a, y, m);
	return c === "equidistantPreserveStart" ? Nk(y, b, g, i, o) : c === "equidistantPreserveEnd" ? Pk(y, b, g, i, o) : (p = c === "preserveStart" || c === "preserveStartEnd" ? Vk(y, b, g, i, o, c === "preserveStartEnd") : Bk(y, b, g, i, o), p.filter((e) => e.isShow));
}
//#endregion
//#region node_modules/recharts/es6/util/YAxisUtils.js
var Uk = (e) => {
	var t = e.ticks, n = e.label, r = e.labelGapWithTick, i = r === void 0 ? 5 : r, a = e.tickSize, o = a === void 0 ? 0 : a, s = e.tickMargin, c = s === void 0 ? 0 : s, l = 0;
	if (t) {
		Array.from(t).forEach((e) => {
			if (e) {
				var t = e.getBoundingClientRect();
				t.width > l && (l = t.width);
			}
		});
		var u = n ? n.getBoundingClientRect().width : 0, d = o + c, f = l + d + u + (n ? i : 0);
		return Math.round(f);
	}
	return 0;
}, Wk = eo({
	name: "renderedTicks",
	initialState: {
		xAxis: {},
		yAxis: {}
	},
	reducers: {
		setRenderedTicks: (e, t) => {
			var n = t.payload, r = n.axisType, i = n.axisId, a = n.ticks;
			e[r][i] = W(a);
		},
		removeRenderedTicks: (e, t) => {
			var n = t.payload, r = n.axisType, i = n.axisId;
			delete e[r][i];
		}
	}
}), Gk = Wk.actions, Kk = Gk.setRenderedTicks, qk = Gk.removeRenderedTicks, Jk = Wk.reducer, Yk = [
	"axisLine",
	"width",
	"height",
	"className",
	"hide",
	"ticks",
	"axisType",
	"axisId"
];
function Xk(e, t) {
	return tA(e) || eA(e, t) || Qk(e, t) || Zk();
}
function Zk() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function Qk(e, t) {
	if (e) {
		if (typeof e == "string") return $k(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? $k(e, t) : void 0;
	}
}
function $k(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function eA(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function tA(e) {
	if (Array.isArray(e)) return e;
}
function nA(e, t) {
	if (e == null) return {};
	var n, r, i = rA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function rA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function iA() {
	return iA = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, iA.apply(null, arguments);
}
function aA(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function oA(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? aA(Object(n), !0).forEach(function(t) {
			sA(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : aA(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function sA(e, t, n) {
	return (t = cA(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function cA(e) {
	var t = lA(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function lA(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var uA = {
	x: 0,
	y: 0,
	width: 0,
	height: 0,
	viewBox: {
		x: 0,
		y: 0,
		width: 0,
		height: 0
	},
	orientation: "bottom",
	ticks: [],
	stroke: "#666",
	tickLine: !0,
	axisLine: !0,
	tick: !0,
	mirror: !1,
	minTickGap: 5,
	tickSize: 6,
	tickMargin: 2,
	interval: "preserveEnd",
	zIndex: np.axis
};
function dA(e) {
	var t = e.x, n = e.y, r = e.width, i = e.height, a = e.orientation, o = e.mirror, s = e.axisLine, c = e.otherSvgProps;
	if (!s) return null;
	var l = oA(oA(oA({}, c), F(s)), {}, { fill: "none" });
	if (a === "top" || a === "bottom") {
		var u = +(a === "top" && !o || a === "bottom" && o);
		l = oA(oA({}, l), {}, {
			x1: t,
			y1: n + u * i,
			x2: t + r,
			y2: n + u * i
		});
	} else {
		var d = +(a === "left" && !o || a === "right" && o);
		l = oA(oA({}, l), {}, {
			x1: t + d * r,
			y1: n,
			x2: t + d * r,
			y2: n + i
		});
	}
	return /*#__PURE__*/ C.createElement("line", iA({}, l, { className: N("recharts-cartesian-axis-line", St(s, "className")) }));
}
function fA(e, t, n, r, i, a, o, s, c) {
	var l, u, d, f, p, m, h = s ? -1 : 1, g = e.tickSize || o, _ = I(e.tickCoord) ? e.tickCoord : e.coordinate;
	switch (a) {
		case "top":
			l = u = e.coordinate, f = n + +!s * i, d = f - h * g, m = d - h * c, p = _;
			break;
		case "left":
			d = f = e.coordinate, u = t + +!s * r, l = u - h * g, p = l - h * c, m = _;
			break;
		case "right":
			d = f = e.coordinate, u = t + +s * r, l = u + h * g, p = l + h * c, m = _;
			break;
		default:
			l = u = e.coordinate, f = n + +s * i, d = f + h * g, m = d + h * c, p = _;
			break;
	}
	return {
		line: {
			x1: l,
			y1: d,
			x2: u,
			y2: f
		},
		tick: {
			x: p,
			y: m
		}
	};
}
function pA(e, t) {
	switch (e) {
		case "left": return t ? "start" : "end";
		case "right": return t ? "end" : "start";
		default: return "middle";
	}
}
function mA(e, t) {
	switch (e) {
		case "left":
		case "right": return "middle";
		case "top": return t ? "start" : "end";
		default: return t ? "end" : "start";
	}
}
function hA(e) {
	var t = e.option, n = e.tickProps, r = e.value, i, a = N(n.className, "recharts-cartesian-axis-tick-value");
	if (/*#__PURE__*/ C.isValidElement(t)) i = /*#__PURE__*/ C.cloneElement(t, oA(oA({}, n), {}, { className: a }));
	else if (typeof t == "function") i = t(oA(oA({}, n), {}, { className: a }));
	else {
		var o = "recharts-cartesian-axis-tick-value";
		typeof t != "boolean" && (o = N(o, yD(t))), i = /*#__PURE__*/ C.createElement(wE, iA({}, n, { className: o }), r);
	}
	return i;
}
function gA(e) {
	var t = e.ticks, n = e.axisType, r = e.axisId, i = R();
	return (0, C.useEffect)(() => r == null || n == null ? Bt : (i(Kk({
		ticks: t.map((e) => ({
			value: e.value,
			coordinate: e.coordinate,
			offset: e.offset,
			index: e.index
		})),
		axisId: r,
		axisType: n
	})), () => {
		i(qk({
			axisId: r,
			axisType: n
		}));
	}), [
		i,
		t,
		r,
		n
	]), null;
}
var _A = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.ticks, r = n === void 0 ? [] : n, i = e.tick, a = e.tickLine, o = e.stroke, s = e.tickFormatter, c = e.unit, l = e.padding, u = e.tickTextProps, d = e.orientation, f = e.mirror, p = e.x, m = e.y, h = e.width, g = e.height, _ = e.tickSize, v = e.tickMargin, y = e.fontSize, b = e.letterSpacing, x = e.getTicksConfig, S = e.events, w = e.axisType, T = e.axisId, E = Hk(oA(oA({}, x), {}, { ticks: r }), y, b), D = F(x), O = ie(i), k = pE(D.textAnchor) ? D.textAnchor : pA(d, f), A = mA(d, f), j = {};
	typeof a == "object" && (j = a);
	var M = oA(oA({}, D), {}, { fill: "none" }, j), P = E.map((e) => oA({ entry: e }, fA(e, p, m, h, g, d, _, f, v))), ee = P.map((e) => {
		var t = e.entry, n = e.line;
		return /*#__PURE__*/ C.createElement(he, {
			className: "recharts-cartesian-axis-tick",
			key: `tick-${t.value}-${t.coordinate}-${t.tickCoord}`
		}, a && /*#__PURE__*/ C.createElement("line", iA({}, M, n, { className: N("recharts-cartesian-axis-tick-line", St(a, "className")) })));
	}), te = P.map((e, t) => {
		var n, r, a = e.entry, d = e.tick, f = oA(oA({}, oA(oA(oA(oA({ verticalAnchor: A }, D), {}, {
			textAnchor: k,
			stroke: "none",
			fill: o
		}, d), {}, {
			index: t,
			payload: a,
			visibleTicksCount: E.length,
			tickFormatter: s,
			padding: l
		}, u), {}, { angle: (n = (r = u == null ? void 0 : u.angle) == null ? D.angle : r) == null ? 0 : n })), O);
		return /*#__PURE__*/ C.createElement(he, iA({
			className: "recharts-cartesian-axis-tick-label",
			key: `tick-label-${a.value}-${a.coordinate}-${a.tickCoord}`
		}, Wt(S, a, t)), i && /*#__PURE__*/ C.createElement(hA, {
			option: i,
			tickProps: f,
			value: `${typeof s == "function" ? s(a.value, t) : a.value}${c || ""}`
		}));
	});
	return /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-ticks recharts-${w}-ticks` }, /*#__PURE__*/ C.createElement(gA, {
		ticks: E,
		axisId: T,
		axisType: w
	}), te.length > 0 && /*#__PURE__*/ C.createElement(dw, { zIndex: np.label }, /*#__PURE__*/ C.createElement("g", {
		className: `recharts-cartesian-axis-tick-labels recharts-${w}-tick-labels`,
		ref: t
	}, te)), ee.length > 0 && /*#__PURE__*/ C.createElement("g", { className: `recharts-cartesian-axis-tick-lines recharts-${w}-tick-lines` }, ee));
}), vA = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.axisLine, r = e.width, i = e.height, a = e.className, o = e.hide, s = e.ticks, c = e.axisType, l = e.axisId, u = nA(e, Yk), d = Xk((0, C.useState)(""), 2), f = d[0], p = d[1], m = Xk((0, C.useState)(""), 2), h = m[0], g = m[1], _ = (0, C.useRef)(null);
	(0, C.useImperativeHandle)(t, () => ({ getCalculatedWidth: () => {
		var t;
		return Uk({
			ticks: _.current,
			label: (t = e.labelRef) == null ? void 0 : t.current,
			labelGapWithTick: 5,
			tickSize: e.tickSize,
			tickMargin: e.tickMargin
		});
	} }));
	var v = (0, C.useCallback)((e) => {
		if (e) {
			var t = e.getElementsByClassName("recharts-cartesian-axis-tick-value");
			_.current = t;
			var n = t[0];
			if (n) {
				var r = window.getComputedStyle(n), i = r.fontSize, a = r.letterSpacing;
				(i !== f || a !== h) && (p(i), g(a));
			}
		}
	}, [f, h]);
	return o || r != null && r <= 0 || i != null && i <= 0 ? null : /*#__PURE__*/ C.createElement(dw, { zIndex: e.zIndex }, /*#__PURE__*/ C.createElement(he, { className: N("recharts-cartesian-axis", a) }, /*#__PURE__*/ C.createElement(dA, {
		x: e.x,
		y: e.y,
		width: r,
		height: i,
		orientation: e.orientation,
		mirror: e.mirror,
		axisLine: n,
		otherSvgProps: F(e)
	}), /*#__PURE__*/ C.createElement(_A, {
		ref: v,
		axisType: c,
		events: u,
		fontSize: f,
		getTicksConfig: e,
		height: e.height,
		letterSpacing: h,
		mirror: e.mirror,
		orientation: e.orientation,
		padding: e.padding,
		stroke: e.stroke,
		tick: e.tick,
		tickFormatter: e.tickFormatter,
		tickLine: e.tickLine,
		tickMargin: e.tickMargin,
		tickSize: e.tickSize,
		tickTextProps: e.tickTextProps,
		ticks: s,
		unit: e.unit,
		width: e.width,
		x: e.x,
		y: e.y,
		axisId: l
	}), /*#__PURE__*/ C.createElement(HE, {
		x: e.x,
		y: e.y,
		width: e.width,
		height: e.height,
		lowerWidth: e.width,
		upperWidth: e.width
	}, /*#__PURE__*/ C.createElement(nD, {
		label: e.label,
		labelRef: e.labelRef
	}), e.children)));
}), yA = /*#__PURE__*/ C.forwardRef((e, t) => {
	var n = Yt(e, uA);
	return /*#__PURE__*/ C.createElement(vA, iA({}, n, { ref: t }));
});
yA.displayName = "CartesianAxis";
//#endregion
//#region node_modules/recharts/es6/state/errorBarSlice.js
var bA = eo({
	name: "errorBars",
	initialState: {},
	reducers: {
		addErrorBar: (e, t) => {
			var n = t.payload, r = n.itemId, i = n.errorBar;
			e[r] || (e[r] = []), e[r].push(i);
		},
		replaceErrorBar: (e, t) => {
			var n = t.payload, r = n.itemId, i = n.prev, a = n.next;
			e[r] && (e[r] = e[r].map((e) => e.dataKey === i.dataKey && e.direction === i.direction ? a : e));
		},
		removeErrorBar: (e, t) => {
			var n = t.payload, r = n.itemId, i = n.errorBar;
			e[r] && (e[r] = e[r].filter((e) => e.dataKey !== i.dataKey || e.direction !== i.direction));
		}
	}
}), xA = bA.actions;
xA.addErrorBar, xA.replaceErrorBar, xA.removeErrorBar;
var SA = bA.reducer, CA = ["children"];
function wA(e, t) {
	if (e == null) return {};
	var n, r, i = TA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function TA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var EA = /*#__PURE__*/ (0, C.createContext)({
	data: [],
	xAxisId: "xAxis-0",
	yAxisId: "yAxis-0",
	dataPointFormatter: () => ({
		x: 0,
		y: 0,
		value: 0
	}),
	errorBarOffset: 0
});
function DA(e) {
	var t = e.children, n = wA(e, CA);
	return /*#__PURE__*/ C.createElement(EA.Provider, { value: n }, t);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/GraphicalItemClipPath.js
function OA(e, t) {
	var n, r, i = z((t) => Ly(t, e)), a = z((e) => By(e, t)), o = (n = i == null ? void 0 : i.allowDataOverflow) == null ? Fy.allowDataOverflow : n, s = (r = a == null ? void 0 : a.allowDataOverflow) == null ? Ry.allowDataOverflow : r;
	return {
		needClip: o || s,
		needClipX: o,
		needClipY: s
	};
}
function kA(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.clipPathId, i = KO(), a = OA(t, n), o = a.needClipX, s = a.needClipY, c = a.needClip, l = z((e) => ux(e, t, !1)), u = z((e) => dx(e, n, !1));
	if (!c || !i) return null;
	var d = i.x, f = i.y, p = i.width, m = i.height, h = o && l ? Math.min(l[0], l[1]) : d - p / 2, g = s && u ? Math.min(u[0], u[1]) : f - m / 2, _ = o && l ? Math.abs(l[1] - l[0]) : p * 2, v = s && u ? Math.abs(u[1] - u[0]) : m * 2;
	return /*#__PURE__*/ C.createElement("clipPath", { id: `clipPath-${r}` }, /*#__PURE__*/ C.createElement("rect", {
		x: h,
		y: g,
		width: _,
		height: v
	}));
}
//#endregion
//#region node_modules/recharts/es6/state/selectors/graphicalItemSelectors.js
function AA(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.xAxisId) == null ? 0 : n;
}
function jA(e, t) {
	var n, r;
	return (n = (r = e.graphicalItems.cartesianItems.find((e) => e.id === t)) == null ? void 0 : r.yAxisId) == null ? 0 : n;
}
//#endregion
//#region node_modules/tiny-invariant/dist/esm/tiny-invariant.js
var MA = "Invariant failed";
function NA(e, t) {
	if (!e) throw Error(MA);
}
//#endregion
//#region node_modules/recharts/es6/util/BarUtils.js
var PA = ["option"];
function FA(e, t) {
	if (e == null) return {};
	var n, r, i = IA(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function IA(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var LA = Nd;
function RA(e) {
	var t = e.option, n = FA(e, PA);
	return /*#__PURE__*/ C.createElement(LD, {
		option: t,
		DefaultShape: LA,
		shapeProps: n,
		activeClassName: "recharts-active-bar",
		inActiveClassName: "recharts-inactive-bar"
	});
}
var zA = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : 0;
	return (n, r) => {
		if (I(e)) return e;
		var i = I(n) || Lt(n);
		return i ? e(n, r) : (!i && NA(!1, `minPointSize callback function received a value with type of ${typeof n}. Currently only numbers or null/undefined are supported.`), t);
	};
}, BA = (e, t, n) => n, VA = B([Jy, (e, t) => t], (e, t) => e.filter((e) => e.type === "bar").find((e) => e.id === t)), HA = B([VA], (e) => e == null ? void 0 : e.maxBarSize), UA = (e, t, n, r) => r, WA = B([
	Y,
	Jy,
	AA,
	jA,
	BA
], (e, t, n, r, i) => t.filter((t) => e === "horizontal" ? t.xAxisId === n : t.yAxisId === r).filter((e) => e.isPanorama === i).filter((e) => e.hide === !1).filter((e) => e.type === "bar")), GA = (e, t, n) => {
	var r = Y(e), i = AA(e, t), a = jA(e, t);
	if (!(i == null || a == null)) return r === "horizontal" ? bb(e, "yAxis", a, n) : bb(e, "xAxis", i, n);
}, KA = B([
	WA,
	Yf,
	(e, t) => {
		var n = Y(e), r = AA(e, t), i = jA(e, t);
		if (!(r == null || i == null)) return n === "horizontal" ? Nx(e, "xAxis", r) : Nx(e, "yAxis", i);
	}
], ek), qA = (e, t, n) => {
	var r, i, a = VA(e, t);
	if (a == null) return 0;
	var o = AA(e, t), s = jA(e, t);
	if (o == null || s == null) return 0;
	var c = Y(e), l = Kf(e), u = a.maxBarSize, d = Lt(u) ? l : u, f, p;
	return c === "horizontal" ? (f = Rx(e, "xAxis", o, n), p = Lx(e, "xAxis", o, n)) : (f = Rx(e, "yAxis", s, n), p = Lx(e, "yAxis", s, n)), (r = (i = gs(f, p, !0)) == null ? d : i) == null ? 0 : r;
}, JA = (e, t, n) => {
	var r = Y(e), i = AA(e, t), a = jA(e, t);
	if (!(i == null || a == null)) {
		var o, s;
		return r === "horizontal" ? (o = Rx(e, "xAxis", i, n), s = Lx(e, "xAxis", i, n)) : (o = Rx(e, "yAxis", a, n), s = Lx(e, "yAxis", a, n)), gs(o, s);
	}
}, YA = B([
	Rs,
	Bs,
	(e, t, n) => {
		var r = AA(e, t);
		if (r != null) return Rx(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = jA(e, t);
		if (r != null) return Rx(e, "yAxis", r, n);
	},
	(e, t, n) => {
		var r = AA(e, t);
		if (r != null) return Lx(e, "xAxis", r, n);
	},
	(e, t, n) => {
		var r = jA(e, t);
		if (r != null) return Lx(e, "yAxis", r, n);
	},
	B([B([
		KA,
		Kf,
		qf,
		Jf,
		qA,
		JA,
		HA
	], sk), VA], lk),
	Y,
	vf,
	JA,
	B([GA, VA], ck),
	VA,
	UA
], (e, t, n, r, i, a, o, s, c, l, u, d, f) => {
	var p = c.chartData, m = c.dataStartIndex, h = c.dataEndIndex;
	if (!(d == null || o == null || t == null || s !== "horizontal" && s !== "vertical" || n == null || r == null || i == null || a == null || l == null)) {
		var g = d.data, _ = g != null && g.length > 0 ? g : p == null ? void 0 : p.slice(m, h + 1);
		if (_ != null) return Rj({
			layout: s,
			barSettings: d,
			pos: o,
			parentViewBox: t,
			bandSize: l,
			xAxis: n,
			yAxis: r,
			xAxisTicks: i,
			yAxisTicks: a,
			stackedData: u,
			displayedData: _,
			offset: e,
			cells: f,
			dataStartIndex: m
		});
	}
}), XA = ["index"];
function ZA() {
	return ZA = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, ZA.apply(null, arguments);
}
function QA(e, t) {
	if (e == null) return {};
	var n, r, i = $A(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function $A(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var ej = /*#__PURE__*/ (0, C.createContext)(void 0), tj = (e) => {
	var t = (0, C.useContext)(ej);
	if (t != null) return t.stackId;
	if (e != null) return cs(e);
}, nj = (e, t) => `recharts-bar-stack-clip-path-${e}-${t}`, rj = (e) => {
	var t = (0, C.useContext)(ej);
	if (t != null) {
		var n = t.stackId;
		return `url(#${nj(n, e)})`;
	}
}, ij = (e) => {
	var t = e.index, n = QA(e, XA), r = rj(t);
	return /*#__PURE__*/ C.createElement(he, ZA({
		className: "recharts-bar-stack-layer",
		clipPath: r
	}, n));
}, aj = [
	"onMouseEnter",
	"onMouseLeave",
	"onClick"
], oj = [
	"value",
	"background",
	"tooltipPosition"
], sj = ["id"], cj = [
	"onMouseEnter",
	"onClick",
	"onMouseLeave"
];
function lj(e, t) {
	return mj(e) || pj(e, t) || dj(e, t) || uj();
}
function uj() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function dj(e, t) {
	if (e) {
		if (typeof e == "string") return fj(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? fj(e, t) : void 0;
	}
}
function fj(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function pj(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function mj(e) {
	if (Array.isArray(e)) return e;
}
function hj() {
	return hj = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, hj.apply(null, arguments);
}
function gj(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function _j(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? gj(Object(n), !0).forEach(function(t) {
			vj(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : gj(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function vj(e, t, n) {
	return (t = yj(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function yj(e) {
	var t = bj(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function bj(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function xj(e, t) {
	if (e == null) return {};
	var n, r, i = Sj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Sj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var Cj = (e) => {
	var t = e.dataKey, n = e.name, r = e.fill, i = e.legendType;
	return [{
		inactive: e.hide,
		dataKey: t,
		type: i,
		color: r,
		value: vs(n, t),
		payload: e
	}];
}, wj = /*#__PURE__*/ C.memo((e) => {
	var t = e.dataKey, n = e.stroke, r = e.strokeWidth, i = e.fill, a = e.name, o = e.hide, s = e.unit, c = e.formatter, l = e.tooltipType, u = e.id, d = {
		dataDefinedOnItem: void 0,
		getPosition: Bt,
		settings: {
			stroke: n,
			strokeWidth: r,
			fill: i,
			dataKey: t,
			nameKey: void 0,
			name: vs(a, t),
			hide: o,
			type: l,
			color: i,
			unit: s,
			formatter: c,
			graphicalItemId: u
		}
	};
	return /*#__PURE__*/ C.createElement(VD, { tooltipEntrySettings: d });
});
function Tj(e) {
	var t = z(sC), n = e.data, r = e.dataKey, i = e.background, a = e.allOtherBarProps, o = a.onMouseEnter, s = a.onMouseLeave, c = a.onClick, l = xj(a, aj), u = RD(o, r, a.id), d = zD(s), f = BD(c, r, a.id);
	if (!i || n == null) return null;
	var p = ie(i);
	return /*#__PURE__*/ C.createElement(dw, { zIndex: uk(i, np.barBackground) }, n.map((e, n) => {
		e.value;
		var a = e.background;
		e.tooltipPosition;
		var o = xj(e, oj);
		if (!a) return null;
		var s = u(e, e.originalDataIndex), c = d(e, e.originalDataIndex), m = f(e, e.originalDataIndex), h = _j(_j(_j(_j(_j({
			option: i,
			isActive: String(e.originalDataIndex) === t
		}, o), {}, { fill: "#eee" }, a), p), Wt(l, e, n)), {}, {
			onMouseEnter: s,
			onMouseLeave: c,
			onClick: m,
			dataKey: r,
			index: n,
			className: "recharts-bar-background-rectangle"
		});
		return /*#__PURE__*/ C.createElement(RA, hj({ key: `background-bar-${n}` }, h));
	}));
}
function Ej(e) {
	var t = e.showLabels, n = e.children, r = e.rects, i = r == null ? void 0 : r.map((e) => {
		var t = {
			x: e.x,
			y: e.y,
			width: e.width,
			lowerWidth: e.width,
			upperWidth: e.width,
			height: e.height
		};
		return _j(_j({}, t), {}, {
			value: e.value,
			payload: e.payload,
			parentViewBox: e.parentViewBox,
			viewBox: t,
			fill: e.fill
		});
	});
	return /*#__PURE__*/ C.createElement(uD, { value: t ? i : void 0 }, n);
}
function Dj(e) {
	var t = e.shape, n = e.activeBar, r = e.baseProps, i = e.entry, a = e.index, o = e.dataKey, s = z(sC), c = z(lC), l = n && String(i.originalDataIndex) === s && (c == null || o === c), u = lj((0, C.useState)(!1), 2), d = u[0], f = u[1], p = lj((0, C.useState)(!1), 2), m = p[0], h = p[1];
	(0, C.useEffect)(() => {
		var e;
		return l ? (f(!0), e = requestAnimationFrame(() => {
			h(!0);
		})) : h(!1), () => {
			cancelAnimationFrame(e);
		};
	}, [l]);
	var g = (0, C.useCallback)(() => {
		l || f(!1);
	}, [l]), _ = l && m, v = l || d, y = l ? n === !0 ? t : n : t, b = /*#__PURE__*/ C.createElement(RA, hj({}, r, { name: String(r.name) }, i, {
		isActive: _,
		option: y,
		index: a,
		dataKey: o,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance,
		onTransitionEnd: g
	}));
	return v ? /*#__PURE__*/ C.createElement(dw, { zIndex: np.activeBar }, /*#__PURE__*/ C.createElement(ij, { index: i.originalDataIndex }, b)) : b;
}
function Oj(e) {
	var t = e.shape, n = e.baseProps, r = e.entry, i = e.index, a = e.dataKey;
	return /*#__PURE__*/ C.createElement(RA, hj({}, n, { name: String(n.name) }, r, {
		isActive: !1,
		option: t,
		index: i,
		dataKey: a,
		animationElapsedTime: e.animationElapsedTime,
		isAnimating: e.isAnimating,
		isEntrance: e.isEntrance
	}));
}
function kj(e) {
	var t, n = e.data, r = e.props, i = e.animationElapsedTime, a = e.isAnimating, o = e.isEntrance, s = (t = F(r)) == null ? {} : t, c = s.id, l = xj(s, sj), u = r.shape, d = r.dataKey, f = r.activeBar, p = r.onMouseEnter, m = r.onClick, h = r.onMouseLeave, g = xj(r, cj), _ = RD(p, d, c), v = zD(h), y = BD(m, d, c);
	return n ? /*#__PURE__*/ C.createElement(C.Fragment, null, n.map((e, t) => /*#__PURE__*/ C.createElement(ij, hj({
		index: e.originalDataIndex,
		key: `rectangle-${e == null ? void 0 : e.x}-${e == null ? void 0 : e.y}-${e == null ? void 0 : e.value}-${t}`,
		className: "recharts-bar-rectangle"
	}, Wt(g, e, t), {
		onMouseEnter: _(e, e.originalDataIndex),
		onMouseLeave: v(e, e.originalDataIndex),
		onClick: y(e, e.originalDataIndex)
	}), f ? /*#__PURE__*/ C.createElement(Dj, {
		shape: u,
		activeBar: f,
		baseProps: l,
		entry: e,
		index: t,
		dataKey: d,
		animationElapsedTime: i,
		isAnimating: a,
		isEntrance: o
	}) : /*#__PURE__*/ C.createElement(Oj, {
		shape: u,
		baseProps: l,
		entry: e,
		index: t,
		dataKey: d,
		animationElapsedTime: i,
		isAnimating: a,
		isEntrance: o
	})))) : null;
}
var Aj = (e, t, n) => e == null ? [] : t === 1 ? e.flatMap((e) => e.status === "removed" ? [] : [e.next]) : e.flatMap((e) => {
	if (e.status === "removed") return n === "horizontal" ? [_j(_j({}, e.prev), {}, {
		height: Ft(e.prev.height, 0, t),
		y: Ft(e.prev.y, e.prev.y + e.prev.height, t)
	})] : [_j(_j({}, e.prev), {}, { width: Ft(e.prev.width, 0, t) })];
	if (e.status === "matched") return [_j(_j({}, e.next), {}, {
		x: Ft(e.prev.x, e.next.x, t),
		y: Ft(e.prev.y, e.next.y, t),
		width: Ft(e.prev.width, e.next.width, t),
		height: Ft(e.prev.height, e.next.height, t)
	})];
	var r = e.next;
	return n === "horizontal" ? [_j(_j({}, r), {}, {
		height: Ft(0, r.height, t),
		y: Ft(r.stackedBarStart, r.y, t)
	})] : [_j(_j({}, r), {}, {
		width: Ft(0, r.width, t),
		x: Ft(r.stackedBarStart, r.x, t)
	})];
});
function jj(e) {
	var t = e.props, n = e.previousRectanglesRef, r = t.data, i = t.isAnimationActive, a = t.animationBegin, o = t.animationDuration, s = t.animationEasing, c = t.animationInterpolateFn, l = t.layout, u = uO(t.onAnimationStart, t.onAnimationEnd), d = u.isAnimating, f = u.handleAnimationStart, p = u.handleAnimationEnd;
	return /*#__PURE__*/ C.createElement(Ej, {
		showLabels: !d,
		rects: r
	}, /*#__PURE__*/ C.createElement(dO, {
		animationInput: r,
		animationIdPrefix: "recharts-bar-",
		items: r,
		previousItemsRef: n,
		isAnimationActive: i,
		animationBegin: a,
		animationDuration: o,
		animationEasing: s,
		onAnimationStart: f,
		onAnimationEnd: p,
		animationInterpolateFn: c,
		animationMatchBy: t.animationMatchBy,
		layout: l
	}, (e, n, r) => /*#__PURE__*/ C.createElement(he, null, /*#__PURE__*/ C.createElement(kj, {
		props: t,
		data: e,
		animationElapsedTime: n,
		isAnimating: d || n < 1,
		isEntrance: r
	}))), /*#__PURE__*/ C.createElement(hD, { label: t.label }), t.children);
}
function Mj(e) {
	var t = (0, C.useRef)(null);
	return /*#__PURE__*/ C.createElement(jj, {
		previousRectanglesRef: t,
		props: e
	});
}
var Nj = 0, Pj = (e, t) => {
	var n = Array.isArray(e.value) ? e.value[1] : e.value;
	return {
		x: e.x,
		y: e.y,
		value: n,
		errorVal: ns(e, t)
	};
}, Fj = class extends C.PureComponent {
	render() {
		var e = this.props, t = e.hide, n = e.data, r = e.dataKey, i = e.className, a = e.xAxisId, o = e.yAxisId, s = e.needClip, c = e.background, l = e.id;
		if (t || n == null) return null;
		var u = N("recharts-bar", i), d = l;
		return /*#__PURE__*/ C.createElement(he, {
			className: u,
			id: l
		}, s && /*#__PURE__*/ C.createElement("defs", null, /*#__PURE__*/ C.createElement(kA, {
			clipPathId: d,
			xAxisId: a,
			yAxisId: o
		})), /*#__PURE__*/ C.createElement(he, {
			className: "recharts-bar-rectangles",
			clipPath: s ? `url(#clipPath-${d})` : void 0
		}, /*#__PURE__*/ C.createElement(Tj, {
			data: n,
			dataKey: r,
			background: c,
			allOtherBarProps: this.props
		}), /*#__PURE__*/ C.createElement(Mj, this.props)));
	}
}, Ij = {
	activeBar: !1,
	animationBegin: 0,
	animationDuration: 400,
	animationEasing: "ease",
	animationInterpolateFn: Aj,
	animationMatchBy: XD,
	background: !1,
	hide: !1,
	isAnimationActive: "auto",
	label: !1,
	legendType: "rect",
	minPointSize: Nj,
	shape: LA,
	xAxisId: 0,
	yAxisId: 0,
	zIndex: np.bar
};
function Lj(e) {
	var t = e.xAxisId, n = e.yAxisId, r = e.hide, i = e.legendType, a = e.minPointSize, o = e.activeBar, s = e.animationBegin, c = e.animationDuration, l = e.animationEasing, u = e.isAnimationActive, d = OA(t, n).needClip, f = kc(), p = Hs(), m = ED(e.children, dT), h = z((t) => YA(t, e.id, p, m));
	if (f !== "vertical" && f !== "horizontal") return null;
	var g, _ = h == null ? void 0 : h[0];
	return g = _ == null || _.height == null || _.width == null ? 0 : f === "vertical" ? _.height / 2 : _.width / 2, /*#__PURE__*/ C.createElement(DA, {
		xAxisId: t,
		yAxisId: n,
		data: h,
		dataPointFormatter: Pj,
		errorBarOffset: g
	}, /*#__PURE__*/ C.createElement(Fj, hj({}, e, {
		layout: f,
		needClip: d,
		data: h,
		xAxisId: t,
		yAxisId: n,
		hide: r,
		legendType: i,
		minPointSize: a,
		activeBar: o,
		animationBegin: s,
		animationDuration: c,
		animationEasing: l,
		isAnimationActive: u
	})));
}
function Rj(e) {
	var t = e.layout, n = e.barSettings, r = n.dataKey, i = n.minPointSize, a = n.hasCustomShape, o = e.pos, s = e.bandSize, c = e.xAxis, l = e.yAxis, u = e.xAxisTicks, d = e.yAxisTicks, f = e.stackedData, p = e.displayedData, m = e.offset, h = e.cells, g = e.parentViewBox, _ = e.dataStartIndex, v = t === "horizontal" ? l : c, y = f ? v.scale.domain() : null, b = us({ numericAxis: v }), x = v.scale.map(b);
	return p.map((e, n) => {
		var p, v, S, C, w, T;
		if (f) {
			var E = f[n + _];
			if (E == null) return null;
			p = as(E, y);
		} else p = ns(e, r), Array.isArray(p) || (p = [b, p]);
		var D = zA(i, Nj)(p[1], n);
		if (t === "horizontal") {
			var O, k = l.scale.map(p[0]), A = l.scale.map(p[1]);
			if (k == null || A == null) return null;
			v = ls({
				axis: c,
				ticks: u,
				bandSize: s,
				offset: o.offset,
				entry: e,
				index: n
			}), S = (O = A == null ? k : A) == null ? void 0 : O, C = o.size;
			var j = k - A;
			if (w = Ot(j) ? 0 : j, T = {
				x: v,
				y: m.top,
				width: C,
				height: m.height
			}, Math.abs(D) > 0 && Math.abs(w) < Math.abs(D)) {
				var M = Dt(w || D) * (Math.abs(D) - Math.abs(w));
				S -= M, w += M;
			}
		} else {
			var N = c.scale.map(p[0]), P = c.scale.map(p[1]);
			if (N == null || P == null) return null;
			if (v = N, S = ls({
				axis: l,
				ticks: d,
				bandSize: s,
				offset: o.offset,
				entry: e,
				index: n
			}), C = P - N, w = o.size, T = {
				x: m.left,
				y: S,
				width: m.width,
				height: w
			}, Math.abs(D) > 0 && Math.abs(C) < Math.abs(D)) {
				var ee = Dt(C || D) * (Math.abs(D) - Math.abs(C));
				C += ee;
			}
		}
		return v == null || S == null || C == null || w == null || !a && (C === 0 || w === 0) ? null : _j(_j({}, e), {}, {
			stackedBarStart: x,
			x: v,
			y: S,
			width: C,
			height: w,
			value: f ? p : p[1],
			payload: e,
			background: T,
			tooltipPosition: {
				x: v + C / 2,
				y: S + w / 2
			},
			parentViewBox: g,
			originalDataIndex: n
		}, h && h[n] && h[n].props);
	}).filter(Boolean);
}
function zj(e) {
	var t = Yt(e, Ij), n = tj(t.stackId), r = Hs();
	return /*#__PURE__*/ C.createElement(SO, {
		id: t.id,
		type: "bar"
	}, (e) => /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(HD, { legendPayload: Cj(t) }), /*#__PURE__*/ C.createElement(wj, {
		dataKey: t.dataKey,
		stroke: t.stroke,
		strokeWidth: t.strokeWidth,
		fill: t.fill,
		name: t.name,
		hide: t.hide,
		unit: t.unit,
		formatter: t.formatter,
		tooltipType: t.tooltipType,
		id: e
	}), /*#__PURE__*/ C.createElement(kO, {
		type: "bar",
		id: e,
		data: void 0,
		xAxisId: t.xAxisId,
		yAxisId: t.yAxisId,
		zAxisId: 0,
		dataKey: t.dataKey,
		stackId: n,
		hide: t.hide,
		barSize: t.barSize,
		minPointSize: t.minPointSize,
		maxBarSize: t.maxBarSize,
		isPanorama: r,
		hasCustomShape: t.shape != null && t.shape !== LA
	}), /*#__PURE__*/ C.createElement(dw, { zIndex: t.zIndex }, /*#__PURE__*/ C.createElement(Lj, hj({}, t, { id: e })))));
}
var Bj = /*#__PURE__*/ C.memo(zj, rl);
Bj.displayName = "Bar";
//#endregion
//#region node_modules/recharts/es6/util/axisPropsAreEqual.js
var Vj = ["domain", "range"], Hj = ["domain", "range"];
function Uj(e, t) {
	if (e == null) return {};
	var n, r, i = Wj(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function Wj(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function Gj(e, t) {
	return e === t ? !0 : Array.isArray(e) && e.length === 2 && Array.isArray(t) && t.length === 2 ? e[0] === t[0] && e[1] === t[1] : !1;
}
function Kj(e, t) {
	if (e === t) return !0;
	var n = e.domain, r = e.range, i = Uj(e, Vj), a = t.domain, o = t.range, s = Uj(t, Hj);
	return !Gj(n, a) || !Gj(r, o) ? !1 : rl(i, s);
}
//#endregion
//#region node_modules/recharts/es6/cartesian/XAxis.js
var qj = ["type"], Jj = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], Yj = ["id", "scale"];
function Xj() {
	return Xj = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, Xj.apply(null, arguments);
}
function Zj(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function Qj(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? Zj(Object(n), !0).forEach(function(t) {
			$j(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : Zj(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function $j(e, t, n) {
	return (t = eM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function eM(e) {
	var t = tM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function tM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function nM(e, t) {
	if (e == null) return {};
	var n, r, i = rM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function rM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function iM(e) {
	var t = R(), n = (0, C.useRef)(null), r = Ac(), i = e.type, a = nM(e, qj), o = op(r, "xAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return Qj(Qj({}, a), {}, { type: o });
	}, [a, o]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(LO(s)) : n.current !== s && t(RO({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(zO(n.current)), n.current = null);
	}, [t]), null;
}
var aM = (e) => {
	var t = e.xAxisId, n = e.className, r = z(Bs), i = Hs(), a = "xAxis", o = z((e) => Ix(e, a, t, i)), s = z((e) => Tx(e, t)), c = z((e) => Ax(e, t)), l = z((e) => Iy(e, t));
	if (s == null || c == null || l == null) return null;
	e.dangerouslySetInnerHTML, e.ticks, e.scale;
	var u = nM(e, Jj);
	l.id, l.scale;
	var d = nM(l, Yj);
	return /*#__PURE__*/ C.createElement(yA, Xj({}, u, d, {
		x: c.x,
		y: c.y,
		width: s.width,
		height: s.height,
		className: N(`recharts-${a} ${a}`, n),
		viewBox: r,
		ticks: o,
		axisType: a,
		axisId: t
	}));
}, oM = {
	allowDataOverflow: Fy.allowDataOverflow,
	allowDecimals: Fy.allowDecimals,
	allowDuplicatedCategory: Fy.allowDuplicatedCategory,
	angle: Fy.angle,
	axisLine: uA.axisLine,
	height: Fy.height,
	hide: !1,
	includeHidden: Fy.includeHidden,
	interval: Fy.interval,
	label: !1,
	minTickGap: Fy.minTickGap,
	mirror: Fy.mirror,
	orientation: Fy.orientation,
	padding: Fy.padding,
	reversed: Fy.reversed,
	scale: Fy.scale,
	tick: Fy.tick,
	tickCount: Fy.tickCount,
	tickLine: uA.tickLine,
	tickSize: uA.tickSize,
	type: Fy.type,
	niceTicks: Fy.niceTicks,
	xAxisId: 0
}, sM = /*#__PURE__*/ C.memo((e) => {
	var t = Yt(e, oM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(iM, {
		allowDataOverflow: t.allowDataOverflow,
		allowDecimals: t.allowDecimals,
		allowDuplicatedCategory: t.allowDuplicatedCategory,
		angle: t.angle,
		dataKey: t.dataKey,
		domain: t.domain,
		height: t.height,
		hide: t.hide,
		id: t.xAxisId,
		includeHidden: t.includeHidden,
		interval: t.interval,
		minTickGap: t.minTickGap,
		mirror: t.mirror,
		name: t.name,
		orientation: t.orientation,
		padding: t.padding,
		reversed: t.reversed,
		scale: t.scale,
		tick: t.tick,
		tickCount: t.tickCount,
		tickFormatter: t.tickFormatter,
		ticks: t.ticks,
		type: t.type,
		unit: t.unit,
		niceTicks: t.niceTicks
	}), /*#__PURE__*/ C.createElement(aM, t));
}, Kj);
sM.displayName = "XAxis";
//#endregion
//#region node_modules/recharts/es6/cartesian/YAxis.js
var cM = ["type"], lM = [
	"dangerouslySetInnerHTML",
	"ticks",
	"scale"
], uM = ["id", "scale"];
function dM() {
	return dM = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, dM.apply(null, arguments);
}
function fM(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function pM(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? fM(Object(n), !0).forEach(function(t) {
			mM(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : fM(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function mM(e, t, n) {
	return (t = hM(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function hM(e) {
	var t = gM(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function gM(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function _M(e, t) {
	if (e == null) return {};
	var n, r, i = vM(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function vM(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function yM(e) {
	var t = R(), n = (0, C.useRef)(null), r = Ac(), i = e.type, a = _M(e, cM), o = op(r, "yAxis", i), s = (0, C.useMemo)(() => {
		if (o != null) return pM(pM({}, a), {}, { type: o });
	}, [o, a]);
	return (0, C.useLayoutEffect)(() => {
		s != null && (n.current === null ? t(BO(s)) : n.current !== s && t(VO({
			prev: n.current,
			next: s
		})), n.current = s);
	}, [s, t]), (0, C.useLayoutEffect)(() => () => {
		n.current && (t(HO(n.current)), n.current = null);
	}, [t]), null;
}
function bM(e) {
	var t = e.yAxisId, n = e.className, r = e.width, i = e.label, a = (0, C.useRef)(null), o = (0, C.useRef)(null), s = z(Bs), c = Hs(), l = R(), u = "yAxis", d = z((e) => Mx(e, t)), f = z((e) => jx(e, t)), p = z((e) => Ix(e, u, t, c)), m = z((e) => zy(e, t));
	if ((0, C.useLayoutEffect)(() => {
		if (!(r !== "auto" || !d || qE(i) || /*#__PURE__*/ (0, C.isValidElement)(i) || m == null)) {
			var e = a.current;
			if (e) {
				var n = e.getCalculatedWidth();
				Math.round(d.width) !== Math.round(n) && l(UO({
					id: t,
					width: n
				}));
			}
		}
	}, [
		p,
		d,
		l,
		i,
		t,
		r,
		m
	]), d == null || f == null || m == null) return null;
	e.dangerouslySetInnerHTML, e.ticks, e.scale;
	var h = _M(e, lM);
	m.id, m.scale;
	var g = _M(m, uM);
	return /*#__PURE__*/ C.createElement(yA, dM({}, h, g, {
		ref: a,
		labelRef: o,
		x: f.x,
		y: f.y,
		tickTextProps: r === "auto" ? { width: void 0 } : { width: r },
		width: d.width,
		height: d.height,
		className: N(`recharts-${u} ${u}`, n),
		viewBox: s,
		ticks: p,
		axisType: u,
		axisId: t
	}));
}
var xM = {
	allowDataOverflow: Ry.allowDataOverflow,
	allowDecimals: Ry.allowDecimals,
	allowDuplicatedCategory: Ry.allowDuplicatedCategory,
	angle: Ry.angle,
	axisLine: uA.axisLine,
	hide: !1,
	includeHidden: Ry.includeHidden,
	interval: Ry.interval,
	label: !1,
	minTickGap: Ry.minTickGap,
	mirror: Ry.mirror,
	orientation: Ry.orientation,
	padding: Ry.padding,
	reversed: Ry.reversed,
	scale: Ry.scale,
	tick: Ry.tick,
	tickCount: Ry.tickCount,
	tickLine: uA.tickLine,
	tickSize: uA.tickSize,
	type: Ry.type,
	niceTicks: Ry.niceTicks,
	width: Ry.width,
	yAxisId: 0
}, SM = /*#__PURE__*/ C.memo((e) => {
	var t = Yt(e, xM);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(yM, {
		interval: t.interval,
		id: t.yAxisId,
		scale: t.scale,
		type: t.type,
		domain: t.domain,
		allowDataOverflow: t.allowDataOverflow,
		dataKey: t.dataKey,
		allowDuplicatedCategory: t.allowDuplicatedCategory,
		allowDecimals: t.allowDecimals,
		tickCount: t.tickCount,
		padding: t.padding,
		includeHidden: t.includeHidden,
		reversed: t.reversed,
		ticks: t.ticks,
		width: t.width,
		orientation: t.orientation,
		mirror: t.mirror,
		hide: t.hide,
		unit: t.unit,
		name: t.name,
		angle: t.angle,
		minTickGap: t.minTickGap,
		tick: t.tick,
		tickFormatter: t.tickFormatter,
		niceTicks: t.niceTicks
	}), /*#__PURE__*/ C.createElement(bM, t));
}, Kj);
SM.displayName = "YAxis";
var CM = B([
	(e, t) => t,
	Y,
	Sp,
	jp,
	eC,
	nC,
	PC,
	Rs
], KC);
//#endregion
//#region node_modules/recharts/es6/util/getRelativeCoordinate.js
function wM(e) {
	return "getBBox" in e.currentTarget && typeof e.currentTarget.getBBox == "function";
}
function TM(e) {
	var t = e.currentTarget.getBoundingClientRect(), n, r;
	if (wM(e)) {
		var i = e.currentTarget.getBBox();
		n = i.width > 0 ? t.width / i.width : 1, r = i.height > 0 ? t.height / i.height : 1;
	} else {
		var a = e.currentTarget;
		n = a.offsetWidth > 0 ? t.width / a.offsetWidth : 1, r = a.offsetHeight > 0 ? t.height / a.offsetHeight : 1;
	}
	var o = (e, i) => ({
		relativeX: Math.round((e - t.left) / n),
		relativeY: Math.round((i - t.top) / r)
	});
	return "touches" in e ? Array.from(e.touches).map((e) => o(e.clientX, e.clientY)) : o(e.clientX, e.clientY);
}
//#endregion
//#region node_modules/recharts/es6/state/mouseEventsMiddleware.js
var EM = Na("mouseClick"), DM = Bo();
DM.startListening({
	actionCreator: EM,
	effect: (e, t) => {
		var n = e.payload, r = CM(t.getState(), TM(n));
		(r == null ? void 0 : r.activeIndex) != null && t.dispatch(aS({
			activeIndex: r.activeIndex,
			activeDataKey: void 0,
			activeCoordinate: r.activeCoordinate
		}));
	}
});
var OM = Na("mouseMove"), kM = Bo(), AM = null, jM = null, MM = null;
kM.startListening({
	actionCreator: OM,
	effect: (e, t) => {
		var n = e.payload, r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || (a == null ? void 0 : a.includes("mousemove"));
		AM !== null && (cancelAnimationFrame(AM), AM = null), jM !== null && (typeof i != "number" || !o) && (clearTimeout(jM), jM = null), MM = TM(n);
		var s = () => {
			var e = t.getState(), n = Ux(e, e.tooltip.settings.shared);
			if (!MM) {
				AM = null, jM = null;
				return;
			}
			if (n === "axis") {
				var r = CM(e, MM);
				(r == null ? void 0 : r.activeIndex) == null ? t.dispatch(nS()) : t.dispatch(iS({
					activeIndex: r.activeIndex,
					activeDataKey: void 0,
					activeCoordinate: r.activeCoordinate
				}));
			}
			AM = null, jM = null;
		};
		if (!o) {
			s();
			return;
		}
		i === "raf" ? AM = requestAnimationFrame(s) : typeof i == "number" && jM === null && (jM = setTimeout(s, i));
	}
});
//#endregion
//#region node_modules/recharts/es6/state/reduxDevtoolsJsonStringifyReplacer.js
function NM(e, t) {
	return t instanceof HTMLElement ? `HTMLElement <${t.tagName} class="${t.className}">` : t === window ? "global.window" : e === "children" && typeof t == "object" && t ? "<<CHILDREN>>" : t;
}
//#endregion
//#region node_modules/recharts/es6/state/rootPropsSlice.js
var PM = {
	accessibilityLayer: !0,
	barCategoryGap: "10%",
	barGap: 4,
	barSize: void 0,
	className: void 0,
	maxBarSize: void 0,
	stackOffset: "none",
	syncId: void 0,
	syncMethod: "index",
	baseValue: void 0,
	reverseStackOrder: !1
}, FM = eo({
	name: "rootProps",
	initialState: PM,
	reducers: { updateOptions: (e, t) => {
		var n;
		e.accessibilityLayer = t.payload.accessibilityLayer, e.barCategoryGap = t.payload.barCategoryGap, e.barGap = (n = t.payload.barGap) == null ? PM.barGap : n, e.barSize = t.payload.barSize, e.maxBarSize = t.payload.maxBarSize, e.stackOffset = t.payload.stackOffset, e.syncId = t.payload.syncId, e.syncMethod = t.payload.syncMethod, e.className = t.payload.className, e.baseValue = t.payload.baseValue, e.reverseStackOrder = t.payload.reverseStackOrder;
	} }
}), IM = FM.reducer, LM = FM.actions.updateOptions, RM = eo({
	name: "polarOptions",
	initialState: null,
	reducers: { updatePolarOptions: (e, t) => e === null ? t.payload : (e.startAngle = t.payload.startAngle, e.endAngle = t.payload.endAngle, e.cx = t.payload.cx, e.cy = t.payload.cy, e.innerRadius = t.payload.innerRadius, e.outerRadius = t.payload.outerRadius, e) }
});
RM.actions.updatePolarOptions;
var zM = RM.reducer, BM = Na("keyDown"), VM = Na("focus"), HM = Na("blur"), UM = Bo(), WM = null, GM = null, KM = null;
UM.startListening({
	actionCreator: BM,
	effect: (e, t) => {
		KM = e.payload, WM !== null && (cancelAnimationFrame(WM), WM = null);
		var n = t.getState().eventSettings, r = n.throttleDelay, i = n.throttledEvents, a = i === "all" || i.includes("keydown");
		GM !== null && (typeof r != "number" || !a) && (clearTimeout(GM), GM = null);
		var o = () => {
			try {
				var e = t.getState();
				if (e.rootProps.accessibilityLayer === !1) return;
				var n = e.tooltip.keyboardInteraction, r = KM;
				if (r !== "ArrowRight" && r !== "ArrowLeft" && r !== "Enter") return;
				var i = bS(n, HS(e), _b(e), ZS(e)), a = i == null ? -1 : Number(i), o = !Number.isFinite(a) || a < 0, s = nC(e), c = HS(e), l = Ux(e, e.tooltip.settings.shared);
				if (r === "Enter") {
					if (o) return;
					var u = zC(e, l, "hover", String(n.index));
					t.dispatch(sS({
						active: !n.active,
						activeIndex: n.index,
						activeCoordinate: u
					}));
					return;
				}
				var d = zx(e) === "left-to-right" ? 1 : -1, f = r === "ArrowRight" ? 1 : -1, p;
				if (o) {
					var m = _b(e), h = ZS(e), g = f * d, _ = (e) => ({
						active: !1,
						index: String(e),
						dataKey: void 0,
						graphicalItemId: void 0,
						coordinate: void 0
					});
					if (p = -1, g > 0) {
						for (var v = 0; v < c.length; v++) if (bS(_(v), c, m, h) != null) {
							p = v;
							break;
						}
					} else for (var y = c.length - 1; y >= 0; y--) if (bS(_(y), c, m, h) != null) {
						p = y;
						break;
					}
					if (p < 0) return;
				} else {
					p = a + f * d;
					var b = (s == null ? void 0 : s.length) || c.length;
					if (b === 0 || p >= b || p < 0) return;
				}
				var x = zC(e, l, "hover", String(p));
				t.dispatch(sS({
					active: !0,
					activeIndex: p.toString(),
					activeCoordinate: x
				}));
			} finally {
				WM = null, GM = null;
			}
		};
		if (!a) {
			o();
			return;
		}
		r === "raf" ? WM = requestAnimationFrame(o) : typeof r == "number" && GM === null && (o(), KM = null, GM = setTimeout(() => {
			KM ? o() : (GM = null, WM = null);
		}, r));
	}
}), UM.startListening({
	actionCreator: VM,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			if (!r.active && r.index == null) {
				var i = "0", a = zC(n, Ux(n, n.tooltip.settings.shared), "hover", String(i));
				t.dispatch(sS({
					active: !0,
					activeIndex: i,
					activeCoordinate: a
				}));
			}
		}
	}
}), UM.startListening({
	actionCreator: HM,
	effect: (e, t) => {
		var n = t.getState();
		if (n.rootProps.accessibilityLayer !== !1) {
			var r = n.tooltip.keyboardInteraction;
			r.active && t.dispatch(sS({
				active: !1,
				activeIndex: r.index,
				activeCoordinate: r.coordinate
			}));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/util/createEventProxy.js
function qM(e) {
	e.persist();
	var t = e.currentTarget;
	return new Proxy(e, { get: (e, n) => {
		if (n === "currentTarget") return t;
		var r = Reflect.get(e, n);
		return typeof r == "function" ? r.bind(e) : r;
	} });
}
//#endregion
//#region node_modules/recharts/es6/state/externalEventsMiddleware.js
var JM = Na("externalEvent"), YM = Bo(), XM = /* @__PURE__ */ new Map(), ZM = /* @__PURE__ */ new Map(), QM = /* @__PURE__ */ new Map();
YM.startListening({
	actionCreator: JM,
	effect: (e, t) => {
		var n = e.payload, r = n.handler, i = n.reactEvent;
		if (r != null) {
			var a = i.type, o = qM(i);
			QM.set(a, {
				handler: r,
				reactEvent: o
			});
			var s = XM.get(a);
			s !== void 0 && (cancelAnimationFrame(s), XM.delete(a));
			var c = t.getState().eventSettings, l = c.throttleDelay, u = c.throttledEvents, d = u === "all" || (u == null ? void 0 : u.includes(a)), f = ZM.get(a);
			f !== void 0 && (typeof l != "number" || !d) && (clearTimeout(f), ZM.delete(a));
			var p = () => {
				var e = QM.get(a);
				try {
					if (!e) return;
					var n = e.handler, r = e.reactEvent, i = t.getState(), o = {
						activeCoordinate: fC(i),
						activeDataKey: lC(i),
						activeIndex: sC(i),
						activeLabel: cC(i),
						activeTooltipIndex: sC(i),
						isTooltipActive: pC(i)
					};
					n && n(o, r);
				} finally {
					XM.delete(a), ZM.delete(a), QM.delete(a);
				}
			};
			if (!d) {
				p();
				return;
			}
			if (l === "raf") {
				var m = requestAnimationFrame(p);
				XM.set(a, m);
			} else if (typeof l == "number") {
				if (!ZM.has(a)) {
					p();
					var h = setTimeout(p, l);
					ZM.set(a, h);
				}
			} else p();
		}
	}
});
var $M = B([
	B([wS], (e) => e.tooltipItemPayloads),
	(e, t) => t,
	(e, t, n) => n
], (e, t, n) => {
	if (t != null) {
		var r = e.find((e) => e.settings.graphicalItemId === n);
		if (r != null) {
			var i = r.getPosition;
			if (i != null) return i(t);
		}
	}
}), eN = Na("touchMove"), tN = Bo(), nN = null, rN = null, iN = null, aN = null;
tN.startListening({
	actionCreator: eN,
	effect: (e, t) => {
		var n = e.payload;
		if (!(n.touches == null || n.touches.length === 0)) {
			aN = qM(n);
			var r = t.getState().eventSettings, i = r.throttleDelay, a = r.throttledEvents, o = a === "all" || a.includes("touchmove");
			nN !== null && (cancelAnimationFrame(nN), nN = null), rN !== null && (typeof i != "number" || !o) && (clearTimeout(rN), rN = null), iN = Array.from(n.touches).map((e) => TM({
				clientX: e.clientX,
				clientY: e.clientY,
				currentTarget: n.currentTarget
			}));
			var s = () => {
				if (aN != null) {
					var e = t.getState(), n = Ux(e, e.tooltip.settings.shared);
					if (n === "axis") {
						var r, i = (r = iN) == null ? void 0 : r[0];
						if (i == null) {
							nN = null, rN = null;
							return;
						}
						var a = CM(e, i);
						(a == null ? void 0 : a.activeIndex) != null && t.dispatch(iS({
							activeIndex: a.activeIndex,
							activeDataKey: void 0,
							activeCoordinate: a.activeCoordinate
						}));
					} else if (n === "item") {
						var o, s = aN.touches[0];
						if (document.elementFromPoint == null || s == null) return;
						var c = document.elementFromPoint(s.clientX, s.clientY);
						if (!c || !c.getAttribute) return;
						var l = c.getAttribute(Ds), u = (o = c.getAttribute("data-recharts-item-id")) == null ? void 0 : o, d = RS(e).find((e) => e.id === u);
						if (l == null || d == null || u == null) return;
						var f = d.dataKey, p = $M(e, l, u);
						t.dispatch(eS({
							activeDataKey: f,
							activeIndex: l,
							activeCoordinate: p,
							activeGraphicalItemId: u
						}));
					}
					nN = null, rN = null;
				}
			};
			if (!o) {
				s();
				return;
			}
			i === "raf" ? nN = requestAnimationFrame(s) : typeof i == "number" && rN === null && (s(), aN = null, rN = setTimeout(() => {
				aN ? s() : (rN = null, nN = null);
			}, i));
		}
	}
});
//#endregion
//#region node_modules/recharts/es6/state/eventSettingsSlice.js
var oN = {
	throttleDelay: "raf",
	throttledEvents: [
		"mousemove",
		"touchmove",
		"pointermove",
		"scroll",
		"wheel"
	]
}, sN = eo({
	name: "eventSettings",
	initialState: oN,
	reducers: { setEventSettings: (e, t) => {
		t.payload.throttleDelay != null && (e.throttleDelay = t.payload.throttleDelay), t.payload.throttledEvents != null && (e.throttledEvents = W(t.payload.throttledEvents));
	} }
}), cN = sN.actions.setEventSettings, lN = sN.reducer, uN = oi({
	brush: mk,
	cartesianAxis: WO,
	chartData: Iw,
	errorBars: SA,
	eventSettings: lN,
	graphicalItems: OO,
	layout: Jo,
	legend: zc,
	options: kw,
	polarAxis: vD,
	polarOptions: zM,
	referenceElements: yk,
	renderedTicks: Jk,
	rootProps: IM,
	tooltip: cS,
	zIndex: lw
}), dN = function(e) {
	var t = arguments.length > 1 && arguments[1] !== void 0 ? arguments[1] : "Chart";
	return Wa({
		reducer: uN,
		preloadedState: e,
		middleware: (e) => {
			var t;
			return e({
				serializableCheck: !1,
				immutableCheck: ![
					"commonjs",
					"es6",
					"production"
				].includes((t = "es6") == null ? "" : t)
			}).concat([
				DM.middleware,
				kM.middleware,
				UM.middleware,
				YM.middleware,
				tN.middleware
			]);
		},
		enhancers: (e) => {
			var t = e;
			return typeof e == "function" && (t = e()), t.concat(Ha({ type: "raf" }));
		},
		devTools: El.devToolsEnabled && {
			serialize: { replacer: NM },
			name: `recharts-${t}`
		}
	});
};
//#endregion
//#region node_modules/recharts/es6/state/RechartsStoreProvider.js
function fN(e) {
	var t = e.preloadedState, n = e.children, r = e.reduxStoreName, i = Hs(), a = (0, C.useRef)(null);
	if (i) return n;
	a.current == null && (a.current = dN(t, r));
	var o = cr;
	return /*#__PURE__*/ C.createElement(el, {
		context: o,
		store: a.current
	}, n);
}
//#endregion
//#region node_modules/recharts/es6/state/ReportMainChartProps.js
function pN(e) {
	var t = e.layout, n = e.margin, r = R(), i = Hs();
	return (0, C.useEffect)(() => {
		i || (r(Go(t)), r(Wo(n)));
	}, [
		r,
		i,
		t,
		n
	]), null;
}
var mN = /*#__PURE__*/ (0, C.memo)(pN, rl);
//#endregion
//#region node_modules/recharts/es6/state/ReportChartProps.js
function hN(e) {
	var t = R();
	return (0, C.useEffect)(() => {
		t(LM(e));
	}, [t, e]), null;
}
var gN = /*#__PURE__*/ (0, C.memo)((e) => {
	var t = R();
	return (0, C.useEffect)(() => {
		t(cN(e));
	}, [t, e]), null;
}, rl);
//#endregion
//#region node_modules/recharts/es6/zIndex/ZIndexPortal.js
function _N(e) {
	var t = e.zIndex, n = e.isPanorama, r = (0, C.useRef)(null), i = R();
	return (0, C.useLayoutEffect)(() => (r.current && i(sw({
		zIndex: t,
		element: r.current,
		isPanorama: n
	})), () => {
		i(cw({
			zIndex: t,
			isPanorama: n
		}));
	}), [
		i,
		t,
		n
	]), /*#__PURE__*/ C.createElement("g", {
		tabIndex: -1,
		ref: r,
		className: `recharts-zIndex-layer_${t}`
	});
}
function vN(e) {
	var t = e.children, n = e.isPanorama, r = z(JC);
	if (!r || r.length === 0) return t;
	var i = r.filter((e) => e < 0), a = r.filter((e) => e > 0);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, i.map((e) => /*#__PURE__*/ C.createElement(_N, {
		key: e,
		zIndex: e,
		isPanorama: n
	})), t, a.map((e) => /*#__PURE__*/ C.createElement(_N, {
		key: e,
		zIndex: e,
		isPanorama: n
	})));
}
//#endregion
//#region node_modules/recharts/es6/container/RootSurface.js
var yN = ["children"];
function bN(e, t) {
	if (e == null) return {};
	var n, r, i = xN(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function xN(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
function SN() {
	return SN = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, SN.apply(null, arguments);
}
var CN = {
	width: "100%",
	height: "100%",
	display: "block"
}, wN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = Dc(), r = Oc(), i = Jl();
	if (!Xo(n) || !Xo(r)) return null;
	var a = e.children, o = e.otherAttributes, s = e.title, c = e.desc, l, u;
	return o != null && (l = typeof o.tabIndex == "number" ? o.tabIndex : i ? 0 : void 0, u = typeof o.role == "string" ? o.role : i ? "application" : void 0), /*#__PURE__*/ C.createElement(ue, SN({}, o, {
		title: s,
		desc: c,
		role: u,
		tabIndex: l,
		width: n,
		height: r,
		style: CN,
		ref: t
	}), a);
}), TN = (e) => {
	var t = e.children, n = z(Ws);
	if (!n) return null;
	var r = n.width, i = n.height, a = n.y, o = n.x;
	return /*#__PURE__*/ C.createElement(ue, {
		width: r,
		height: i,
		x: o,
		y: a
	}, t);
}, EN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = bN(e, yN);
	return Hs() ? /*#__PURE__*/ C.createElement(TN, null, /*#__PURE__*/ C.createElement(vN, { isPanorama: !0 }, n)) : /*#__PURE__*/ C.createElement(wN, SN({ ref: t }, r), /*#__PURE__*/ C.createElement(vN, { isPanorama: !1 }, n));
});
//#endregion
//#region node_modules/recharts/es6/util/useReportScale.js
function DN(e, t) {
	return MN(e) || jN(e, t) || kN(e, t) || ON();
}
function ON() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function kN(e, t) {
	if (e) {
		if (typeof e == "string") return AN(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? AN(e, t) : void 0;
	}
}
function AN(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function jN(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function MN(e) {
	if (Array.isArray(e)) return e;
}
function NN() {
	var e = R(), t = DN((0, C.useState)(null), 2), n = t[0], r = t[1], i = z(Cs);
	return (0, C.useEffect)(() => {
		if (n != null) {
			var t = n.getBoundingClientRect().width / n.offsetWidth;
			q(t) && t !== i && e(qo(t));
		}
	}, [
		n,
		e,
		i
	]), r;
}
//#endregion
//#region node_modules/recharts/es6/chart/RechartsWrapper.js
function PN(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function FN(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? PN(Object(n), !0).forEach(function(t) {
			IN(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : PN(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function IN(e, t, n) {
	return (t = LN(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function LN(e) {
	var t = RN(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function RN(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
function zN() {
	return zN = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, zN.apply(null, arguments);
}
function BN(e, t) {
	return GN(e) || WN(e, t) || HN(e, t) || VN();
}
function VN() {
	throw TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.");
}
function HN(e, t) {
	if (e) {
		if (typeof e == "string") return UN(e, t);
		var n = {}.toString.call(e).slice(8, -1);
		return n === "Object" && e.constructor && (n = e.constructor.name), n === "Map" || n === "Set" ? Array.from(e) : n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n) ? UN(e, t) : void 0;
	}
}
function UN(e, t) {
	(t == null || t > e.length) && (t = e.length);
	for (var n = 0, r = Array(t); n < t; n++) r[n] = e[n];
	return r;
}
function WN(e, t) {
	var n = e == null ? null : typeof Symbol < "u" && e[Symbol.iterator] || e["@@iterator"];
	if (n != null) {
		var r, i, a, o, s = [], c = !0, l = !1;
		try {
			if (a = (n = n.call(e)).next, t === 0) {
				if (Object(n) !== n) return;
				c = !1;
			} else for (; !(c = (r = a.call(n)).done) && (s.push(r.value), s.length !== t); c = !0);
		} catch (e) {
			l = !0, i = e;
		} finally {
			try {
				if (!c && n.return != null && (o = n.return(), Object(o) !== o)) return;
			} finally {
				if (l) throw i;
			}
		}
		return s;
	}
}
function GN(e) {
	if (Array.isArray(e)) return e;
}
var KN = () => (qw(), null);
function qN(e) {
	if (typeof e == "number") return e;
	if (typeof e == "string") {
		var t = parseFloat(e);
		if (!Number.isNaN(t)) return t;
	}
	return 0;
}
var JN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n, r, i = (0, C.useRef)(null), a = BN((0, C.useState)({
		containerWidth: qN((n = e.style) == null ? void 0 : n.width),
		containerHeight: qN((r = e.style) == null ? void 0 : r.height)
	}), 2), o = a[0], s = a[1], c = (0, C.useCallback)((e, t) => {
		s((n) => {
			var r = Math.round(e), i = Math.round(t);
			return n.containerWidth === r && n.containerHeight === i ? n : {
				containerWidth: r,
				containerHeight: i
			};
		});
	}, []), l = (0, C.useCallback)((e) => {
		if (typeof t == "function" && t(e), i.current != null && (i.current.disconnect(), i.current = null), e != null && typeof ResizeObserver < "u") {
			var n = e.getBoundingClientRect(), r = n.width, a = n.height;
			c(r, a);
			var o = new ResizeObserver((e) => {
				var t = e[0];
				if (t != null) {
					var n = t.contentRect, r = n.width, i = n.height;
					c(r, i);
				}
			});
			o.observe(e), i.current = o;
		}
	}, [t, c]);
	return (0, C.useEffect)(() => () => {
		var e = i.current;
		e != null && e.disconnect();
	}, [c]), /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Nc, {
		width: o.containerWidth,
		height: o.containerHeight
	}), /*#__PURE__*/ C.createElement("div", zN({ ref: l }, e)));
}), YN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = BN((0, C.useState)({
		containerWidth: qN(n),
		containerHeight: qN(r)
	}), 2), a = i[0], o = i[1], s = (0, C.useCallback)((e, t) => {
		o((n) => {
			var r = Math.round(e), i = Math.round(t);
			return n.containerWidth === r && n.containerHeight === i ? n : {
				containerWidth: r,
				containerHeight: i
			};
		});
	}, []), c = (0, C.useCallback)((e) => {
		if (typeof t == "function" && t(e), e != null) {
			var n = e.getBoundingClientRect(), r = n.width, i = n.height;
			s(r, i);
		}
	}, [t, s]);
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Nc, {
		width: a.containerWidth,
		height: a.containerHeight
	}), /*#__PURE__*/ C.createElement("div", zN({ ref: c }, e)));
}), XN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Nc, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", zN({ ref: t }, e)));
}), ZN = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height;
	return typeof n == "string" || typeof r == "string" ? /*#__PURE__*/ C.createElement(YN, zN({}, e, { ref: t })) : typeof n == "number" && typeof r == "number" ? /*#__PURE__*/ C.createElement(XN, zN({}, e, {
		width: n,
		height: r,
		ref: t
	})) : /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Nc, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement("div", zN({ ref: t }, e)));
});
function QN(e) {
	return e ? JN : ZN;
}
var $N = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.children, r = e.className, i = e.height, a = e.onClick, o = e.onContextMenu, s = e.onDoubleClick, c = e.onMouseDown, l = e.onMouseEnter, u = e.onMouseLeave, d = e.onMouseMove, f = e.onMouseUp, p = e.onTouchEnd, m = e.onTouchMove, h = e.onTouchStart, g = e.style, _ = e.width, v = e.responsive, y = e.dispatchTouchEvents, b = y === void 0 || y, x = (0, C.useRef)(null), S = R(), w = BN((0, C.useState)(null), 2), T = w[0], E = w[1], D = BN((0, C.useState)(null), 2), O = D[0], k = D[1], A = NN(), j = bc(), M = (j == null ? void 0 : j.width) > 0 ? j.width : _, P = (j == null ? void 0 : j.height) > 0 ? j.height : i, ee = (0, C.useCallback)((e) => {
		A(e), typeof t == "function" && t(e), E(e), k(e), e != null && (x.current = e);
	}, [
		A,
		t,
		E,
		k
	]), te = (0, C.useCallback)((e) => {
		S(EM(e)), S(JM({
			handler: a,
			reactEvent: e
		}));
	}, [S, a]), ne = (0, C.useCallback)((e) => {
		S(OM(e)), S(JM({
			handler: l,
			reactEvent: e
		}));
	}, [S, l]), re = (0, C.useCallback)((e) => {
		S(nS()), S(JM({
			handler: u,
			reactEvent: e
		}));
	}, [S, u]), F = (0, C.useCallback)((e) => {
		S(OM(e)), S(JM({
			handler: d,
			reactEvent: e
		}));
	}, [S, d]), ie = (0, C.useCallback)(() => {
		S(VM());
	}, [S]), ae = (0, C.useCallback)(() => {
		S(HM());
	}, [S]), oe = (0, C.useCallback)((e) => {
		S(BM(e.key));
	}, [S]), se = (0, C.useCallback)((e) => {
		S(JM({
			handler: o,
			reactEvent: e
		}));
	}, [S, o]), ce = (0, C.useCallback)((e) => {
		S(JM({
			handler: s,
			reactEvent: e
		}));
	}, [S, s]), le = (0, C.useCallback)((e) => {
		S(JM({
			handler: c,
			reactEvent: e
		}));
	}, [S, c]), ue = (0, C.useCallback)((e) => {
		S(JM({
			handler: f,
			reactEvent: e
		}));
	}, [S, f]), de = (0, C.useCallback)((e) => {
		S(JM({
			handler: h,
			reactEvent: e
		}));
	}, [S, h]), fe = (0, C.useCallback)((e) => {
		b && S(eN(e)), S(JM({
			handler: m,
			reactEvent: e
		}));
	}, [
		S,
		b,
		m
	]), pe = (0, C.useCallback)((e) => {
		S(JM({
			handler: p,
			reactEvent: e
		}));
	}, [S, p]), me = QN(v);
	return /*#__PURE__*/ C.createElement(xw.Provider, { value: T }, /*#__PURE__*/ C.createElement(ge.Provider, { value: O }, /*#__PURE__*/ C.createElement(me, {
		width: M == null ? g == null ? void 0 : g.width : M,
		height: P == null ? g == null ? void 0 : g.height : P,
		className: N("recharts-wrapper", r),
		style: FN({
			position: "relative",
			cursor: "default",
			width: M,
			height: P
		}, g),
		onClick: te,
		onContextMenu: se,
		onDoubleClick: ce,
		onFocus: ie,
		onBlur: ae,
		onKeyDown: oe,
		onMouseDown: le,
		onMouseEnter: ne,
		onMouseLeave: re,
		onMouseMove: F,
		onMouseUp: ue,
		onTouchEnd: pe,
		onTouchMove: fe,
		onTouchStart: de,
		ref: ee
	}, /*#__PURE__*/ C.createElement(KN, null), n)));
}), eP = [
	"width",
	"height",
	"responsive",
	"children",
	"className",
	"style",
	"compact",
	"title",
	"desc"
];
function tP(e, t) {
	if (e == null) return {};
	var n, r, i = nP(e, t);
	if (Object.getOwnPropertySymbols) {
		var a = Object.getOwnPropertySymbols(e);
		for (r = 0; r < a.length; r++) n = a[r], t.indexOf(n) === -1 && {}.propertyIsEnumerable.call(e, n) && (i[n] = e[n]);
	}
	return i;
}
function nP(e, t) {
	if (e == null) return {};
	var n = {};
	for (var r in e) if ({}.hasOwnProperty.call(e, r)) {
		if (t.indexOf(r) !== -1) continue;
		n[r] = e[r];
	}
	return n;
}
var rP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => {
	var n = e.width, r = e.height, i = e.responsive, a = e.children, o = e.className, s = e.style, c = e.compact, l = e.title, u = e.desc, d = F(tP(e, eP));
	return c ? /*#__PURE__*/ C.createElement(C.Fragment, null, /*#__PURE__*/ C.createElement(Nc, {
		width: n,
		height: r
	}), /*#__PURE__*/ C.createElement(EN, {
		otherAttributes: d,
		title: l,
		desc: u
	}, a)) : /*#__PURE__*/ C.createElement($N, {
		className: o,
		style: s,
		width: n,
		height: r,
		responsive: i != null && i,
		onClick: e.onClick,
		onMouseLeave: e.onMouseLeave,
		onMouseEnter: e.onMouseEnter,
		onMouseMove: e.onMouseMove,
		onMouseDown: e.onMouseDown,
		onMouseUp: e.onMouseUp,
		onContextMenu: e.onContextMenu,
		onDoubleClick: e.onDoubleClick,
		onTouchStart: e.onTouchStart,
		onTouchMove: e.onTouchMove,
		onTouchEnd: e.onTouchEnd
	}, /*#__PURE__*/ C.createElement(EN, {
		otherAttributes: d,
		title: l,
		desc: u,
		ref: t
	}, /*#__PURE__*/ C.createElement(Dk, null, a)));
});
//#endregion
//#region node_modules/recharts/es6/chart/CartesianChart.js
function iP() {
	return iP = Object.assign ? Object.assign.bind() : function(e) {
		for (var t = 1; t < arguments.length; t++) {
			var n = arguments[t];
			for (var r in n) ({}).hasOwnProperty.call(n, r) && (e[r] = n[r]);
		}
		return e;
	}, iP.apply(null, arguments);
}
function aP(e, t) {
	var n = Object.keys(e);
	if (Object.getOwnPropertySymbols) {
		var r = Object.getOwnPropertySymbols(e);
		t && (r = r.filter(function(t) {
			return Object.getOwnPropertyDescriptor(e, t).enumerable;
		})), n.push.apply(n, r);
	}
	return n;
}
function oP(e) {
	for (var t = 1; t < arguments.length; t++) {
		var n = arguments[t] == null ? {} : arguments[t];
		t % 2 ? aP(Object(n), !0).forEach(function(t) {
			sP(e, t, n[t]);
		}) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(n)) : aP(Object(n)).forEach(function(t) {
			Object.defineProperty(e, t, Object.getOwnPropertyDescriptor(n, t));
		});
	}
	return e;
}
function sP(e, t, n) {
	return (t = cP(t)) in e ? Object.defineProperty(e, t, {
		value: n,
		enumerable: !0,
		configurable: !0,
		writable: !0
	}) : e[t] = n, e;
}
function cP(e) {
	var t = lP(e, "string");
	return typeof t == "symbol" ? t : t + "";
}
function lP(e, t) {
	if (typeof e != "object" || !e) return e;
	var n = e[Symbol.toPrimitive];
	if (n !== void 0) {
		var r = n.call(e, t || "default");
		if (typeof r != "object") return r;
		throw TypeError("@@toPrimitive must return a primitive value.");
	}
	return (t === "string" ? String : Number)(e);
}
var uP = oP({
	accessibilityLayer: !0,
	barCategoryGap: "10%",
	barGap: 4,
	layout: "horizontal",
	margin: {
		top: 5,
		right: 5,
		bottom: 5,
		left: 5
	},
	responsive: !1,
	reverseStackOrder: !1,
	stackOffset: "none",
	syncMethod: "index"
}, oN), dP = /*#__PURE__*/ (0, C.forwardRef)(function(e, t) {
	var n, r = Yt(e.categoricalChartProps, uP), i = e.chartName, a = e.defaultTooltipEventType, o = e.validateTooltipEventTypes, s = e.tooltipPayloadSearcher, c = e.categoricalChartProps, l = {
		chartName: i,
		defaultTooltipEventType: a,
		validateTooltipEventTypes: o,
		tooltipPayloadSearcher: s,
		eventEmitter: void 0
	};
	return /*#__PURE__*/ C.createElement(fN, {
		preloadedState: { options: l },
		reduxStoreName: (n = c.id) == null ? i : n
	}, /*#__PURE__*/ C.createElement(dk, { chartData: c.data }), /*#__PURE__*/ C.createElement(mN, {
		layout: r.layout,
		margin: r.margin
	}), /*#__PURE__*/ C.createElement(gN, {
		throttleDelay: r.throttleDelay,
		throttledEvents: r.throttledEvents
	}), /*#__PURE__*/ C.createElement(hN, {
		baseValue: r.baseValue,
		accessibilityLayer: r.accessibilityLayer,
		barCategoryGap: r.barCategoryGap,
		maxBarSize: r.maxBarSize,
		stackOffset: r.stackOffset,
		barGap: r.barGap,
		barSize: r.barSize,
		syncId: r.syncId,
		syncMethod: r.syncMethod,
		className: r.className,
		reverseStackOrder: r.reverseStackOrder
	}), /*#__PURE__*/ C.createElement(rP, iP({}, r, { ref: t })));
}), fP = ["axis", "item"], pP = /*#__PURE__*/ (0, C.forwardRef)((e, t) => /*#__PURE__*/ C.createElement(dP, {
	chartName: "BarChart",
	defaultTooltipEventType: "axis",
	validateTooltipEventTypes: fP,
	tooltipPayloadSearcher: Dw,
	categoricalChartProps: e,
	ref: t
})), mP = /* @__PURE__ */ o(((e) => {
	var t = d(), n = Symbol.for("react.element"), r = Object.prototype.hasOwnProperty, i = t.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.ReactCurrentOwner, a = {
		key: !0,
		ref: !0,
		__self: !0,
		__source: !0
	};
	function o(e, t, o) {
		var s, c = {}, l = null, u = null;
		for (s in o !== void 0 && (l = "" + o), t.key !== void 0 && (l = "" + t.key), t.ref !== void 0 && (u = t.ref), t) r.call(t, s) && !a.hasOwnProperty(s) && (c[s] = t[s]);
		if (e && e.defaultProps) for (s in t = e.defaultProps, t) c[s] === void 0 && (c[s] = t[s]);
		return {
			$$typeof: n,
			type: e,
			key: l,
			ref: u,
			props: c,
			_owner: i.current
		};
	}
	e.jsx = o, e.jsxs = o;
})), hP = /* @__PURE__ */ o(((e, t) => {
	t.exports = mP();
})), gP = g(), $ = hP(), _P = [
	{
		key: "queueRows",
		label: "Queue Rows",
		icon: A,
		tone: "blue"
	},
	{
		key: "nextSteps",
		label: "Next Steps",
		icon: O,
		tone: "green"
	},
	{
		key: "undecidedJobReviews",
		label: "Undecided Job Reviews",
		icon: k,
		tone: "violet"
	},
	{
		key: "undecidedMaybeTailor",
		label: "Undecided Maybe Tailor",
		icon: j,
		tone: "cyan"
	}
], vP = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
function yP(e) {
	return Number.isFinite(e) ? Math.max(0, Number(e)) : 0;
}
function bP(e) {
	return Number.isFinite(e) ? vP.format(Number(e)) : "—";
}
function xP({ active: e, payload: t }) {
	var n;
	if (!e || !(t != null && t.length)) return null;
	let r = (n = t[0]) == null ? void 0 : n.payload;
	return r ? /* @__PURE__ */ (0, $.jsxs)("div", {
		className: "executive-kpi-tooltip",
		children: [
			/* @__PURE__ */ (0, $.jsx)("span", { children: "Current" }),
			/* @__PURE__ */ (0, $.jsx)("strong", { children: bP(r.current) }),
			Number(r.baseline) > 0 ? /* @__PURE__ */ (0, $.jsxs)("small", { children: ["Queue baseline: ", bP(r.baseline)] }) : null
		]
	}) : null;
}
function SP({ value: e, queueRows: t, label: n }) {
	let r = Math.max(t, e, 1), i = [{
		name: "Current snapshot",
		current: e,
		remaining: Math.max(0, r - e),
		baseline: t
	}];
	return /* @__PURE__ */ (0, $.jsx)("div", {
		className: "executive-kpi-chart",
		role: "img",
		"aria-label": t > 0 ? `${n}: ${bP(e)} against a current queue baseline of ${bP(t)}` : `${n}: ${bP(e)} in the current snapshot`,
		children: /* @__PURE__ */ (0, $.jsx)(Sc, {
			width: "100%",
			height: "100%",
			children: /* @__PURE__ */ (0, $.jsxs)(pP, {
				data: i,
				layout: "vertical",
				margin: {
					top: 6,
					right: 0,
					bottom: 6,
					left: 0
				},
				children: [
					/* @__PURE__ */ (0, $.jsx)(sM, {
						type: "number",
						domain: [0, r],
						hide: !0
					}),
					/* @__PURE__ */ (0, $.jsx)(SM, {
						type: "category",
						dataKey: "name",
						hide: !0
					}),
					/* @__PURE__ */ (0, $.jsx)(uT, {
						content: /* @__PURE__ */ (0, $.jsx)(xP, {}),
						cursor: !1
					}),
					/* @__PURE__ */ (0, $.jsx)(Bj, {
						dataKey: "current",
						stackId: "snapshot",
						fill: "var(--executive-kpi-accent)",
						radius: [
							4,
							0,
							0,
							4
						],
						isAnimationActive: !1
					}),
					/* @__PURE__ */ (0, $.jsx)(Bj, {
						dataKey: "remaining",
						stackId: "snapshot",
						fill: "var(--executive-kpi-track)",
						radius: [
							0,
							4,
							4,
							0
						],
						isAnimationActive: !1
					})
				]
			})
		})
	});
}
function CP({ metric: e }) {
	let t = e.icon;
	return /* @__PURE__ */ (0, $.jsxs)("article", {
		className: `executive-kpi-card executive-kpi-card--${e.tone}`,
		"aria-busy": "true",
		children: [
			/* @__PURE__ */ (0, $.jsxs)("div", {
				className: "executive-kpi-card-header",
				children: [/* @__PURE__ */ (0, $.jsx)("span", {
					className: "executive-kpi-label",
					children: e.label
				}), /* @__PURE__ */ (0, $.jsx)("span", {
					className: "executive-kpi-icon",
					"aria-hidden": "true",
					children: /* @__PURE__ */ (0, $.jsx)(t, {
						size: 17,
						strokeWidth: 2
					})
				})]
			}),
			/* @__PURE__ */ (0, $.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--value" }),
			/* @__PURE__ */ (0, $.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--caption" }),
			/* @__PURE__ */ (0, $.jsx)("div", { className: "executive-kpi-skeleton executive-kpi-skeleton--chart" })
		]
	});
}
function wP({ state: e }) {
	if (e.status === "loading") return /* @__PURE__ */ (0, $.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Loading executive queue metrics",
		children: _P.map((e) => /* @__PURE__ */ (0, $.jsx)(CP, { metric: e }, e.key))
	});
	let t = e.status === "error", n = t ? {
		queueRows: null,
		nextSteps: null,
		undecidedJobReviews: null,
		undecidedMaybeTailor: null
	} : e.metrics, r = yP(n.queueRows);
	return /* @__PURE__ */ (0, $.jsx)("div", {
		className: "executive-kpi-dashboard kpi-grid kpi-grid-cols-1 sm:kpi-grid-cols-2 xl:kpi-grid-cols-4 kpi-gap-3",
		"aria-label": "Executive queue metrics",
		children: _P.map((e) => {
			let i = e.icon, a = n[e.key], o = yP(a);
			return /* @__PURE__ */ (0, $.jsxs)("article", {
				className: `executive-kpi-card executive-kpi-card--${e.tone}`,
				children: [
					/* @__PURE__ */ (0, $.jsxs)("div", {
						className: "executive-kpi-card-header",
						children: [/* @__PURE__ */ (0, $.jsx)("span", {
							className: "executive-kpi-label",
							children: e.label
						}), /* @__PURE__ */ (0, $.jsx)("span", {
							className: "executive-kpi-icon",
							"aria-hidden": "true",
							children: /* @__PURE__ */ (0, $.jsx)(i, {
								size: 17,
								strokeWidth: 2
							})
						})]
					}),
					/* @__PURE__ */ (0, $.jsx)("strong", {
						className: "executive-kpi-value",
						children: t ? "Unavailable" : bP(a)
					}),
					/* @__PURE__ */ (0, $.jsx)("span", {
						className: "executive-kpi-caption",
						children: t ? "Status data could not be loaded" : "Current snapshot"
					}),
					t ? /* @__PURE__ */ (0, $.jsx)("div", {
						className: "executive-kpi-error",
						role: "status",
						children: "Refresh Status to try again."
					}) : /* @__PURE__ */ (0, $.jsx)(SP, {
						value: o,
						queueRows: r,
						label: e.label
					})
				]
			}, e.key);
		})
	});
}
//#endregion
//#region src/main.tsx
var TP = "applylens:executive-kpi-state", EP = { status: "loading" };
function DP() {
	let [e, t] = (0, C.useState)(() => window.__APPLYLENS_EXECUTIVE_KPI_STATE__ || EP);
	return (0, C.useEffect)(() => {
		let e = (e) => {
			let n = e.detail;
			n != null && n.status && t(n);
		};
		return window.addEventListener(TP, e), () => window.removeEventListener(TP, e);
	}, []), /* @__PURE__ */ (0, $.jsx)(wP, { state: e });
}
var OP = document.getElementById("executiveKpiRoot");
OP && (0, gP.createRoot)(OP).render(/* @__PURE__ */ (0, $.jsx)(C.StrictMode, { children: /* @__PURE__ */ (0, $.jsx)(DP, {}) }));
//#endregion

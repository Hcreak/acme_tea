# acme_tea
The Self-use ACME client

Not applicable for all requirement, Special place:
 * Challenge Type Only Use **DNS-01**
 * **Account Private Key** And **Domain Private Key** Only Use EC (Elliptic Curve), Not support RSA
   
   Now also need [Let's Encrypt ECDSA Allowlist Request Form](https://forms.gle/ftKeqkj6AJgXUDPJ8)

## Auto Install
```bash
curl -Lso- https://raw.githubusercontent.com/Hcreak/acme_tea/master/auto.sh | bash
```

## Reference
 * [acme.sh](https://github.com/acmesh-official/acme.sh)
 * [acme-tiny](https://github.com/diafygi/acme-tiny)
 * [acme-dns-tiny](https://github.com/Trim/acme-dns-tiny)
 * https://zhuanlan.zhihu.com/p/75032510 （这个漏洞百出）
 * [draft-ietf-acme-acme.md (RFC8555)](https://github.com/ietf-wg-acme/acme/blob/master/draft-ietf-acme-acme.md) （这个晦涩难懂）

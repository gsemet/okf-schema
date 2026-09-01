// @implements_req SwRS-CORE-002
pub fn export_rust_row(name: &str, value: &str) -> String {
    format!("{name},{value}\n")
}

mod pkg_ops;
mod result;

use std::{env, path::Path};

use crate::{features::package::result::{PackageError, PackageErrorType, PackageOutput, PackageResult}, toolkits, utils::manifest::Manifest};

/// Provisions a package with Flatboat files
pub fn provision_pkg(pkg_name: &String) -> PackageResult {
	let pkg_str_path = "./src/".to_owned() + pkg_name;
	let pkg_path = Path::new(&pkg_str_path);
		
	// Get current workspace Manifest
	let manifest = Manifest::new().ok().ok_or(PackageError {
		kind: PackageErrorType::ManifestNotFound,
		desc: "Unable to find manifest file, please make sure you are in the correct folder"
	})?;

	// Moves inside the package direcctory
	env::set_current_dir(pkg_path).ok().ok_or(PackageError {
		kind: PackageErrorType::PackageCreationError,
		desc: "Unable to open package folder"
	})?;

	// Adds Docker File Configuration
	toolkits::oras::pull_template(&manifest.artifacts.package).ok().ok_or(PackageError {
		kind: PackageErrorType::PackageCreationError,
		desc: "ORAS command failed, unable to pull template from registry"
	})?;

	return Ok(PackageOutput {
		desc: "Successfull package creation"
	});
}
